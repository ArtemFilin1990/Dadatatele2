from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Callable, Generator

import numpy as np
import pandas as pd


EXCLUDE_SHEET_KEYWORDS = ['REF_', 'SCHEMA', 'DICT_', 'CROSSREF_', 'RAW_']
INPUT_WORKBOOKS = ['catalog_full_brands_aprom_enriched.xlsx', 'catalog_full_brands_aprom_patch.xlsx']
CSV_CHUNK_SIZE = 100_000
RETRY_ATTEMPTS = 3
RETRY_BASE_DELAY = 0.25


logger = logging.getLogger(__name__)


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logs."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'time': self.formatTime(record, self.datefmt),
        }
        if record.exc_info:
            payload['exc_info'] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> None:
    """Configure module logger once."""
    if logger.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


def _is_missing(value: object) -> bool:
    """Check whether a value is empty or NaN-like."""
    return value is None or str(value).strip() in {'', 'nan', 'None'}


def _retry(operation_name: str, fn: Callable[[], pd.DataFrame | pd.ExcelFile | list[pd.DataFrame]]) -> pd.DataFrame | pd.ExcelFile | list[pd.DataFrame]:
    """Retry bounded I/O operations with exponential backoff."""
    last_exception: Exception | None = None
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            last_exception = exc
            if attempt == RETRY_ATTEMPTS:
                break
            delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
            logger.warning(
                'operation_retry operation=%s attempt=%d delay_seconds=%.2f',
                operation_name,
                attempt,
                delay,
            )
            time.sleep(delay)
    raise RuntimeError(f'Operation failed after retries: {operation_name}') from last_exception


def read_reference_sheet(input_dir: Path, sheet_name: str) -> pd.DataFrame:
    """Read reference sheet from csv extract or workbook."""
    csv_name = f'catalog_full_brands_aprom_enriched.xlsx - {sheet_name}.csv'
    csv_path = input_dir / csv_name
    if csv_path.exists():
        return _retry(f'read_csv:{csv_path.name}', lambda: pd.read_csv(csv_path, dtype=str, low_memory=False))  # type: ignore[return-value]

    for workbook_name in INPUT_WORKBOOKS:
        workbook_path = input_dir / workbook_name
        if not workbook_path.exists():
            continue
        try:
            excel = _retry(f'open_excel:{workbook_name}', lambda: pd.ExcelFile(workbook_path))
            assert isinstance(excel, pd.ExcelFile)
            if sheet_name in excel.sheet_names:
                result = _retry(
                    f'read_excel:{workbook_name}:{sheet_name}',
                    lambda: pd.read_excel(workbook_path, sheet_name=sheet_name, dtype=str),
                )
                assert isinstance(result, pd.DataFrame)
                return result
        except Exception:  # noqa: BLE001
            logger.exception('reference_sheet_read_failed sheet=%s workbook=%s', sheet_name, workbook_name)
            continue

    return pd.DataFrame()


def read_csv_safely(csv_path: Path) -> pd.DataFrame:
    """Read csv in chunks to reduce peak memory pressure."""
    chunks = _retry(
        f'read_csv_chunks:{csv_path.name}',
        lambda: list(pd.read_csv(csv_path, dtype=str, low_memory=False, chunksize=CSV_CHUNK_SIZE)),
    )
    assert isinstance(chunks, list)
    if not chunks:
        return pd.DataFrame()
    return pd.concat(chunks, ignore_index=True)


def iter_data_frames(input_dir: Path) -> Generator[tuple[str, pd.DataFrame], None, None]:
    """Yield source DataFrames from csv and workbook sheets."""
    exclude_keywords = ['REF_', 'SCHEMA', 'DICT_', 'CROSSREF_', 'MASTER_PRODUCTS', 'RAW_']
    for csv_path in input_dir.glob('*.csv'):
        if any(keyword in csv_path.name for keyword in exclude_keywords):
            continue
        try:
            yield str(csv_path), read_csv_safely(csv_path)
        except Exception:  # noqa: BLE001
            logger.exception('csv_read_failed path=%s', csv_path)

    master_csv = input_dir / 'catalog_full_brands_aprom_enriched.xlsx - MASTER_PRODUCTS.csv'
    if master_csv.exists():
        try:
            yield str(master_csv), read_csv_safely(master_csv)
        except Exception:  # noqa: BLE001
            logger.exception('master_csv_read_failed path=%s', master_csv)

    for workbook_name in INPUT_WORKBOOKS:
        workbook_path = input_dir / workbook_name
        if not workbook_path.exists():
            continue
        try:
            excel = _retry(f'open_excel:{workbook_name}', lambda: pd.ExcelFile(workbook_path))
            assert isinstance(excel, pd.ExcelFile)
        except Exception:  # noqa: BLE001
            logger.exception('workbook_read_failed path=%s', workbook_path)
            continue

        for sheet_name in excel.sheet_names:
            if any(keyword in sheet_name for keyword in EXCLUDE_SHEET_KEYWORDS):
                continue
            try:
                sheet_df = _retry(
                    f'read_excel:{workbook_name}:{sheet_name}',
                    lambda: pd.read_excel(workbook_path, sheet_name=sheet_name, dtype=str),
                )
                assert isinstance(sheet_df, pd.DataFrame)
                yield f'{workbook_name}:{sheet_name}', sheet_df
            except Exception:  # noqa: BLE001
                logger.exception('sheet_read_failed workbook=%s sheet=%s', workbook_name, sheet_name)


def load_references(input_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load and normalize reference tables."""
    ref_sizes = read_reference_sheet(input_dir, 'REF_GOST_ISO_размеры')
    if not ref_sizes.empty:
        for col in ['d', 'D', 'B', 'Масса']:
            if col in ref_sizes.columns:
                ref_sizes[col] = pd.to_numeric(ref_sizes[col].astype(str).str.replace(',', '.'), errors='coerce')

    ref_suffixes = read_reference_sheet(input_dir, 'REF_ISO_суффиксы')
    if not ref_suffixes.empty:
        ref_suffixes.columns = ['Код', 'Расшифровка']
    else:
        ref_suffixes = pd.DataFrame(columns=['Код', 'Расшифровка'])

    return ref_sizes, ref_suffixes


def build_catalogs(input_dir: str, output_file: str) -> None:
    """Build final workbook with GOST/ISO catalog outputs."""
    configure_logging()
    input_path = Path(input_dir)
    output_path = Path(output_file)
    if not input_path.exists():
        raise FileNotFoundError(f'Input directory not found: {input_path}')

    output_path.parent.mkdir(parents=True, exist_ok=True)

    ref_sizes, ref_suffixes = load_references(input_path)

    gost_dict: dict[str, dict[str, object]] = {}
    iso_dict: dict[str, dict[str, object]] = {}

    if not ref_sizes.empty:
        for _, row in ref_sizes.iterrows():
            gost_num = str(row.get('Отечественный', '')).strip()
            iso_num = str(row.get('Импортный', '')).strip()
            data = {
                'd_mm': row.get('d'),
                'D_mm': row.get('D'),
                'B_mm': row.get('B'),
                'M_kg': row.get('Масса'),
            }
            if not _is_missing(gost_num):
                gost_dict[gost_num] = {'analog': iso_num, **data}
            if not _is_missing(iso_num):
                iso_dict[iso_num] = {'analog': gost_num, **data}

    gost_rows: list[list[object]] = []
    iso_rows: list[list[object]] = []
    prefixes: set[str] = set()
    suffixes: set[str] = set()

    columns_to_extract = [
        'Бренд', 'продукция', 'префикс', 'номер', 'суффикс',
        'd_mm', 'D_mm', 'B_mm', 'mass_kg', 'interface', 'Аналог',
    ]

    for source_name, df in iter_data_frames(input_path):
        missing_cols = [col for col in columns_to_extract if col not in df.columns]
        for missing_col in missing_cols:
            df[missing_col] = np.nan

        for _, row in df.iterrows():
            brand = str(row['Бренд']).strip() if pd.notna(row['Бренд']) else ''
            prod = str(row['продукция']).strip() if pd.notna(row['продукция']) else 'Подшипник'
            pref = str(row['префикс']).strip() if pd.notna(row['префикс']) else ''
            num = str(row['номер']).strip() if pd.notna(row['номер']) else ''
            suff = str(row['суффикс']).strip() if pd.notna(row['суффикс']) else ''

            if not _is_missing(pref):
                prefixes.add(pref)
            if not _is_missing(suff):
                suffixes.add(suff)
            if _is_missing(num):
                continue

            interface = str(row['interface']).strip().upper()
            if interface not in ['ГОСТ', 'ISO']:
                if num in gost_dict:
                    interface = 'ГОСТ'
                elif num in iso_dict:
                    interface = 'ISO'
                elif any('А' <= ch <= 'я' or ch in {'Ё', 'ё'} for ch in brand):
                    interface = 'ГОСТ'
                else:
                    interface = 'ISO'

            d_val = pd.to_numeric(str(row['d_mm']).replace(',', '.'), errors='coerce')
            D_val = pd.to_numeric(str(row['D_mm']).replace(',', '.'), errors='coerce')
            B_val = pd.to_numeric(str(row['B_mm']).replace(',', '.'), errors='coerce')
            M_val = pd.to_numeric(str(row['mass_kg']).replace(',', '.'), errors='coerce')

            original_analog = str(row['Аналог']).strip() if pd.notna(row['Аналог']) else ''
            analog_pref, analog_num, analog_suff, analog_full = '', '', '', 'NO DIRECT EQUIV'

            ref_data = gost_dict.get(num) if interface == 'ГОСТ' else iso_dict.get(num)
            if ref_data:
                size_match = True
                if pd.notna(d_val) and pd.notna(ref_data['d_mm']) and not np.isclose(d_val, ref_data['d_mm'], atol=0.01):
                    size_match = False
                if pd.notna(D_val) and pd.notna(ref_data['D_mm']) and not np.isclose(D_val, ref_data['D_mm'], atol=0.01):
                    size_match = False

                if size_match and ref_data['analog'] and ref_data['analog'] != 'nan':
                    analog_num = str(ref_data['analog'])
                    analog_full = analog_num
                    if original_analog and analog_num in original_analog:
                        analog_full = original_analog

                    d_val = d_val if pd.notna(d_val) else ref_data['d_mm']
                    D_val = D_val if pd.notna(D_val) else ref_data['D_mm']
                    B_val = B_val if pd.notna(B_val) else ref_data['B_mm']
                    M_val = M_val if pd.notna(M_val) else ref_data['M_kg']

            row_data = [
                brand, prod, pref, num, suff,
                analog_pref, analog_num, analog_suff, analog_full,
                d_val, D_val, B_val, M_val,
            ]

            if interface == 'ГОСТ':
                gost_rows.append(row_data)
            else:
                iso_rows.append(row_data)

        logger.info('source_processed source=%s rows=%d', source_name, len(df))

    out_cols = [
        'Бренд', 'продукция', 'префикс', 'номер', 'суффикс',
        'префикс аналога', 'номер аналога', 'суффикс аналога', 'Аналог',
        'd мм', 'D мм', 'B мм', 'M кг',
    ]

    dedup_key = ['Бренд', 'префикс', 'номер', 'суффикс', 'Аналог']
    df_gost = pd.DataFrame(gost_rows, columns=out_cols).drop_duplicates(subset=dedup_key)
    df_iso = pd.DataFrame(iso_rows, columns=out_cols).drop_duplicates(subset=dedup_key)

    schema_data = [
        ['Бренд', 'text', 'yes', 'Бренд источника'],
        ['продукция', 'text', 'yes', 'Тип продукции'],
        ['префикс', 'text', 'no', 'Часть обозначения до базового номера'],
        ['номер', 'text', 'yes', 'Базовый номер подшипника'],
        ['суффикс', 'text', 'no', 'Часть обозначения после базового номера'],
        ['префикс аналога', 'text', 'no', 'Префикс обозначения аналога'],
        ['номер аналога', 'text', 'no', 'Базовый номер аналога'],
        ['суффикс аналога', 'text', 'no', 'Суффикс обозначения аналога'],
        ['Аналог', 'text', 'no', 'Полное обозначение прямого аналога'],
        ['d мм', 'number', 'no', 'Внутренний диаметр'],
        ['D мм', 'number', 'no', 'Наружный диаметр'],
        ['B мм', 'number', 'no', 'Ширина'],
        ['M кг', 'number', 'no', 'Масса'],
    ]
    df_schema = pd.DataFrame(schema_data, columns=['field', 'type', 'required', 'description'])

    df_prefix = pd.DataFrame([{'Код': p, 'Расшифровка': ''} for p in sorted(prefixes) if p])

    found_suffixes = pd.DataFrame({'Код': sorted([s for s in suffixes if s])})
    if not ref_suffixes.empty:
        df_suffix = pd.merge(found_suffixes, ref_suffixes, on='Код', how='left').fillna('')
    else:
        df_suffix = found_suffixes
        df_suffix['Расшифровка'] = ''

    with pd.ExcelWriter(output_path) as writer:
        df_gost.to_excel(writer, sheet_name='GOST', index=False)
        df_iso.to_excel(writer, sheet_name='ISO', index=False)
        df_schema.to_excel(writer, sheet_name='SCHEMA', index=False)
        df_prefix.to_excel(writer, sheet_name='PREFIX_DICT', index=False)
        df_suffix.to_excel(writer, sheet_name='SUFFIX_DICT', index=False)

    logger.info(
        'catalog_build_complete output_file=%s gost_rows=%d iso_rows=%d prefix_count=%d suffix_count=%d gost_no_direct_equiv=%d iso_no_direct_equiv=%d',
        output_path,
        len(df_gost),
        len(df_iso),
        len(df_prefix),
        len(df_suffix),
        len(df_gost[df_gost['Аналог'] == 'NO DIRECT EQUIV']),
        len(df_iso[df_iso['Аналог'] == 'NO DIRECT EQUIV']),
    )


if __name__ == '__main__':
    build_catalogs(input_dir='.', output_file='clean/result_catalog.xlsx')
