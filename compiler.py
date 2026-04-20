import glob
import os

import numpy as np
import pandas as pd


EXCLUDE_SHEET_KEYWORDS = ['REF_', 'SCHEMA', 'DICT_', 'CROSSREF_', 'RAW_']


def read_reference_sheet(input_dir: str, sheet_name: str) -> pd.DataFrame:
    csv_name = f'catalog_full_brands_aprom_enriched.xlsx - {sheet_name}.csv'
    csv_path = os.path.join(input_dir, csv_name)
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path, dtype=str)

    for workbook_name in ['catalog_full_brands_aprom_enriched.xlsx', 'catalog_full_brands_aprom_patch.xlsx']:
        workbook_path = os.path.join(input_dir, workbook_name)
        if not os.path.exists(workbook_path):
            continue
        try:
            excel = pd.ExcelFile(workbook_path)
            if sheet_name in excel.sheet_names:
                return pd.read_excel(workbook_path, sheet_name=sheet_name, dtype=str)
        except Exception:
            continue

    return pd.DataFrame()


def iter_data_frames(input_dir: str):
    all_csvs = glob.glob(os.path.join(input_dir, '*.csv'))
    exclude_keywords = ['REF_', 'SCHEMA', 'DICT_', 'CROSSREF_', 'MASTER_PRODUCTS', 'RAW_']
    for csv_path in all_csvs:
        if any(x in os.path.basename(csv_path) for x in exclude_keywords):
            continue
        try:
            yield csv_path, pd.read_csv(csv_path, dtype=str, low_memory=False)
        except Exception as e:
            print(f'Ошибка чтения {csv_path}: {e}')

    master_csv = os.path.join(input_dir, 'catalog_full_brands_aprom_enriched.xlsx - MASTER_PRODUCTS.csv')
    if os.path.exists(master_csv):
        try:
            yield master_csv, pd.read_csv(master_csv, dtype=str, low_memory=False)
        except Exception as e:
            print(f'Ошибка чтения {master_csv}: {e}')

    for workbook_name in ['catalog_full_brands_aprom_enriched.xlsx', 'catalog_full_brands_aprom_patch.xlsx']:
        workbook_path = os.path.join(input_dir, workbook_name)
        if not os.path.exists(workbook_path):
            continue
        try:
            excel = pd.ExcelFile(workbook_path)
        except Exception as e:
            print(f'Ошибка чтения {workbook_path}: {e}')
            continue

        for sheet_name in excel.sheet_names:
            if any(x in sheet_name for x in EXCLUDE_SHEET_KEYWORDS):
                continue
            try:
                sheet_df = pd.read_excel(workbook_path, sheet_name=sheet_name, dtype=str)
                yield f'{workbook_name}:{sheet_name}', sheet_df
            except Exception as e:
                print(f'Ошибка чтения {workbook_name}:{sheet_name}: {e}')


def load_references(input_dir: str):
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


def build_catalogs(input_dir: str, output_file: str):
    ref_sizes, ref_suffixes = load_references(input_dir)

    gost_dict = {}
    iso_dict = {}

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
            if gost_num and gost_num != 'nan':
                gost_dict[gost_num] = {'analog': iso_num, **data}
            if iso_num and iso_num != 'nan':
                iso_dict[iso_num] = {'analog': gost_num, **data}

    gost_rows = []
    iso_rows = []
    prefixes = set()
    suffixes = set()

    columns_to_extract = [
        'Бренд', 'продукция', 'префикс', 'номер', 'суффикс',
        'd_mm', 'D_mm', 'B_mm', 'mass_kg', 'interface', 'Аналог'
    ]

    for _, df in iter_data_frames(input_dir):
        missing_cols = [c for c in columns_to_extract if c not in df.columns]
        for mc in missing_cols:
            df[mc] = np.nan

        for _, row in df.iterrows():
            brand = str(row['Бренд']).strip() if pd.notna(row['Бренд']) else ''
            prod = str(row['продукция']).strip() if pd.notna(row['продукция']) else 'Подшипник'
            pref = str(row['префикс']).strip() if pd.notna(row['префикс']) else ''
            num = str(row['номер']).strip() if pd.notna(row['номер']) else ''
            suff = str(row['суффикс']).strip() if pd.notna(row['суффикс']) else ''

            if pref and pref != 'nan':
                prefixes.add(pref)
            if suff and suff != 'nan':
                suffixes.add(suff)

            if not num or num == 'nan':
                continue

            interface = str(row['interface']).strip().upper()
            if interface not in ['ГОСТ', 'ISO']:
                if num in gost_dict:
                    interface = 'ГОСТ'
                elif num in iso_dict:
                    interface = 'ISO'
                elif any('А' <= ch <= 'я' or ch == 'Ё' or ch == 'ё' for ch in brand):
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
                    analog_num = ref_data['analog']
                    analog_full = analog_num
                    if original_analog and str(analog_num) in original_analog:
                        analog_full = original_analog

                    d_val = d_val if pd.notna(d_val) else ref_data['d_mm']
                    D_val = D_val if pd.notna(D_val) else ref_data['D_mm']
                    B_val = B_val if pd.notna(B_val) else ref_data['B_mm']
                    M_val = M_val if pd.notna(M_val) else ref_data['M_kg']

            row_data = [
                brand, prod, pref, num, suff,
                analog_pref, analog_num, analog_suff, analog_full,
                d_val, D_val, B_val, M_val
            ]

            if interface == 'ГОСТ':
                gost_rows.append(row_data)
            else:
                iso_rows.append(row_data)

    out_cols = [
        'Бренд', 'продукция', 'префикс', 'номер', 'суффикс',
        'префикс аналога', 'номер аналога', 'суффикс аналога', 'Аналог',
        'd мм', 'D мм', 'B мм', 'M кг'
    ]

    df_gost = pd.DataFrame(gost_rows, columns=out_cols).drop_duplicates()
    df_iso = pd.DataFrame(iso_rows, columns=out_cols).drop_duplicates()

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

    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        df_gost.to_excel(writer, sheet_name='GOST', index=False)
        df_iso.to_excel(writer, sheet_name='ISO', index=False)
        df_schema.to_excel(writer, sheet_name='SCHEMA', index=False)
        df_prefix.to_excel(writer, sheet_name='PREFIX_DICT', index=False)
        df_suffix.to_excel(writer, sheet_name='SUFFIX_DICT', index=False)

    print('--- КРАТКИЙ ОТЧЁТ ---')
    print(f'Строк в GOST: {len(df_gost)}')
    print(f'Строк в ISO: {len(df_iso)}')
    print(f'Кодов в PREFIX_DICT: {len(df_prefix)}')
    print(f'Кодов в SUFFIX_DICT: {len(df_suffix)}')
    print(f"NO DIRECT EQUIV в GOST: {len(df_gost[df_gost['Аналог'] == 'NO DIRECT EQUIV'])}")
    print(f"NO DIRECT EQUIV в ISO: {len(df_iso[df_iso['Аналог'] == 'NO DIRECT EQUIV'])}")


if __name__ == '__main__':
    build_catalogs(input_dir='.', output_file='result_catalog.xlsx')
