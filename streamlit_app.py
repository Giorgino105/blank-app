
#WEB-WEB-WEB-WEB-WEB-WEB-WEB-WEB-WEB-WEB-WEB-WEB
#WEB-WEB-WEB-WEB-WEB-WEB-WEB-WEB-WEB-WEB-WEB-WEB
#WEB-WEB-WEB-WEB-WEB-WEB-WEB-WEB-WEB-WEB-WEB-WEB

# Código principal (ejecutar en otra celda)

  
import streamlit as st
import pandas as pd
import io
from pathlib import Path
from math import ceil
import hashlib
import subprocess
import threading
import time

# Configuración de autenticación
VALID_PASSWORDS = {
    "JR": "admin",
    "MEG": "admin",
    "JM": "admin",
    "JJJ": "admin",
    "JAS": "admin",
    "AM": "admin",
    "RA": "admin",
    "MS": "admin",  
    # Agrega más usuarios aquí
}

def check_password():
    """Manejo de autenticación"""
    def password_entered():
        username = st.session_state["username"]
        password = st.session_state["password"]
        
        if username in VALID_PASSWORDS and VALID_PASSWORDS[username] == password:
            st.session_state["password_correct"] = True
            st.session_state["current_user"] = username
            del st.session_state["password"]  # No guardar la contraseña
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # Primera vez, mostrar inputs
        st.title("🔐 Acceso al Calculador SMC")
        st.text_input("Usuario", key="username")
        st.text_input("Contraseña", type="password", key="password", on_change=password_entered)
        return False
    elif not st.session_state["password_correct"]:
        # Contraseña incorrecta
        st.title("🔐 Acceso al Calculador SMC")
        st.text_input("Usuario", key="username")
        st.text_input("Contraseña", type="password", key="password", on_change=password_entered)
        st.error("Usuario o contraseña incorrectos")
        return False
    else:
        # Contraseña correcta
        return True

# [Resto del código sin cambios - todas las funciones permanecen igual]
@st.cache_data
def load_catalog_with_limits_web(catalog_df, families_df):
    """Versión adaptada para web de la función de carga de catálogo"""
    fam_limits, fam_protocols = process_families_data(families_df)
    mod_df = process_module_data(catalog_df)
    return mod_df, fam_limits, fam_protocols

def process_families_data(df):
    """Procesa los datos de familias"""
    df.columns = df.columns.str.strip()

    # Buscar la fila que contiene "Familia"
    familia_row_idx = None
    for idx, row in df.iterrows():
        if any('Familia' in str(cell) for cell in row):
            familia_row_idx = idx
            break

    if familia_row_idx is None:
        familia_row_idx = 0

    # Usar esa fila como nombres de familias
    familia_names = df.iloc[familia_row_idx].fillna('').astype(str).tolist()

    # Buscar la fila que contiene "Max_Modulos"
    max_modulos_row_idx = None
    for idx, row in df.iterrows():
        if any('Max_Modulos' in str(cell) for cell in row):
            max_modulos_row_idx = idx
            break

    # Buscar la fila que contiene información de protocolos
    protocolo_row_idx = None
    for idx, row in df.iterrows():
        if any('Protocolo' in str(cell) for cell in row):
            protocolo_row_idx = idx
            break

    # Procesar límites de módulos
    if max_modulos_row_idx is None:
        fam_limits = {"EX500": 4, "EX600": 9, "EXW1": 9}
    else:
        max_modulos_values = df.iloc[max_modulos_row_idx].fillna(0).tolist()
        fam_limits = {}
        for i, (familia, max_mod) in enumerate(zip(familia_names, max_modulos_values)):
            familia = str(familia).strip()
            if familia and familia != 'Familia' and len(familia) > 2:
                try:
                    max_mod_int = int(float(max_mod))
                    if max_mod_int > 0:
                        fam_limits[familia] = max_mod_int
                except (ValueError, TypeError):
                    continue

    # Procesar protocolos de comunicación
    if protocolo_row_idx is None:
        fam_protocols = {
            "EX500": ["DeviceNet", "CC-Link"],
            "EX600": ["EtherNet/IP", "Profinet", "EtherCAT"],
            "EXW1": ["IO-Link Wireless"]
        }
    else:
        protocolo_values = df.iloc[protocolo_row_idx].fillna('').astype(str).tolist()
        fam_protocols = {}
        for i, (familia, protocolo) in enumerate(zip(familia_names, protocolo_values)):
            familia = str(familia).strip()
            if familia and familia != 'Familia' and len(familia) > 2:
                if protocolo and protocolo.strip():
                    separadores = [',', ';', '|', '/']
                    protocolos_lista = [protocolo.strip()]

                    for sep in separadores:
                        if sep in protocolo:
                            protocolos_lista = [p.strip() for p in protocolo.split(sep) if p.strip()]
                            break

                    fam_protocols[familia] = protocolos_lista
                else:
                    fam_protocols[familia] = ["Sin especificar"]

    if not fam_limits:
        fam_limits = {"EX500": 4, "EX600": 9, "EXW1": 9}

    if not fam_protocols:
        fam_protocols = {
            "EX500": ["DeviceNet", "CC-Link"],
            "EX600": ["EtherNet/IP", "Profinet", "EtherCAT"],
            "EXW1": ["IO-Link Wireless"]
        }

    return fam_limits, fam_protocols

def process_module_data(df):
    """Procesa y limpia los datos de módulos del DataFrame"""
    # Si los datos están en formato horizontal, los transponemos
    if 'Columna' in df.columns or df.iloc[0, 0] == 'Columna':
        df = df.T
        df.columns = df.iloc[0]
        df = df[1:]
        df.reset_index(drop=True, inplace=True)

    # Renombrar columnas para consistencia
    column_mapping = {
        'Columna': 'Referencia',
        'Familia': 'Familia',
        'Referencia': 'Referencia',
        'Tipo': 'Tipo',
        'Entradas_DI': 'Entradas_DI',
        'Salidas_DO': 'Salidas_DO',
        'IO_Link_Ports': 'IO_Link_Ports',
        'Analog_In': 'Analog_In',
        'Analog_Out': 'Analog_Out',
        'Conector': 'Conector',
        'Wireless': 'Wireless',
        'Polaridad': 'Polaridad',
        'Precio': 'Precio'
    }

    for old_name, new_name in column_mapping.items():
        if old_name in df.columns:
            df.rename(columns={old_name: new_name}, inplace=True)

    if 'Referencia' not in df.columns:
        if df.index.name:
            df['Referencia'] = df.index
        else:
            df['Referencia'] = df.iloc[:, 0]

    df = df.fillna(0)

    # Convertir columnas numéricas
    numeric_columns = ["Entradas_DI", "Salidas_DO", "IO_Link_Ports", "Analog_In", "Analog_Out", "Precio"]
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Convertir columnas booleanas
    if 'Wireless' in df.columns:
        df['Wireless'] = df['Wireless'].astype(str).str.upper().isin(['TRUE', 'YES', '1', 'SI'])
    else:
        df['Wireless'] = False

    # Asegurar que las columnas necesarias existen
    required_columns = ['Referencia', 'Familia', 'Tipo', 'Entradas_DI', 'Salidas_DO', 'IO_Link_Ports', 'Precio']
    for col in required_columns:
        if col not in df.columns:
            if col == 'Familia':
                df[col] = 'EX600'
            elif col == 'Tipo':
                df[col] = 'DI'
            else:
                df[col] = 0

    return df

def filter_families_by_protocol(df, fam_limits, fam_protocols, selected_protocol):
    """Filtra las familias según el protocolo seleccionado"""
    compatible_families = []

    for familia, protocolos in fam_protocols.items():
        if selected_protocol in protocolos:
            compatible_families.append(familia)

    if not compatible_families:
        return df, fam_limits, []

    # Filtrar el DataFrame de módulos
    filtered_df = df[df["Familia"].isin(compatible_families)]

    # Filtrar los límites de familias
    filtered_limits = {fam: fam_limits[fam] for fam in compatible_families if fam in fam_limits}

    return filtered_df, filtered_limits, compatible_families

def calculate_zone_modules(fam_df, di_needed, do_needed, iol_needed):
    """Calcula los módulos necesarios para una zona específica"""
    if di_needed <= 0 and do_needed <= 0 and iol_needed <= 0:
        return [], 0, None

    def calculate_module_priority(mod):
        priority = 0
        if 'Polaridad' in mod.index:
            if str(mod['Polaridad']).upper() == 'PNP':
                priority += 0
            else:
                priority += 1000
        priority += mod['Precio']
        return priority

    all_mods = fam_df.copy()
    all_mods['priority'] = all_mods.apply(calculate_module_priority, axis=1)
    all_mods = all_mods.sort_values('priority')

    best_solution = None
    best_cost = float('inf')
    best_modules_count = float('inf')

    # Estrategia con módulos mixtos
    mixed_solutions = []

    for _, mod in all_mods.iterrows():
        di_cap = mod['Entradas_DI']
        do_cap = mod['Salidas_DO']
        iol_cap = mod['IO_Link_Ports']

        if di_cap <= 0 and do_cap <= 0 and iol_cap <= 0:
            continue

        if di_cap > 0 and do_cap > 0:  # Módulo mixto DI/DO
            needed_for_di = ceil(di_needed / di_cap) if di_needed > 0 else 0
            needed_for_do = ceil(do_needed / do_cap) if do_needed > 0 else 0
            needed_mixed = max(needed_for_di, needed_for_do)

            if needed_mixed > 0:
                di_covered = min(di_needed, needed_mixed * di_cap)
                do_covered = min(do_needed, needed_mixed * do_cap)

                remaining_di = max(0, di_needed - di_covered)
                remaining_do = max(0, do_needed - do_covered)
                remaining_iol = iol_needed

                mixed_solutions.append({
                    'modules': [(mod, needed_mixed)],
                    'remaining_di': remaining_di,
                    'remaining_do': remaining_do,
                    'remaining_iol': remaining_iol,
                    'cost': mod['Precio'] * needed_mixed,
                    'count': needed_mixed
                })

    # Evaluar soluciones mixtas y completar
    for mix_sol in mixed_solutions:
        total_modules = mix_sol['modules'].copy()
        total_cost = mix_sol['cost']
        total_count = mix_sol['count']

        # Completar DI restantes
        if mix_sol['remaining_di'] > 0:
            di_mods = all_mods[all_mods['Entradas_DI'] > 0]
            for _, mod in di_mods.iterrows():
                needed = ceil(mix_sol['remaining_di'] / mod['Entradas_DI'])
                total_modules.append((mod, needed))
                total_cost += mod['Precio'] * needed
                total_count += needed
                break

        # Completar DO restantes
        if mix_sol['remaining_do'] > 0:
            do_mods = all_mods[all_mods['Salidas_DO'] > 0]
            for _, mod in do_mods.iterrows():
                needed = ceil(mix_sol['remaining_do'] / mod['Salidas_DO'])
                total_modules.append((mod, needed))
                total_cost += mod['Precio'] * needed
                total_count += needed
                break

        # Completar IO-Link
        if mix_sol['remaining_iol'] > 0:
            iol_mods = all_mods[all_mods['IO_Link_Ports'] > 0]
            for _, mod in iol_mods.iterrows():
                needed = ceil(mix_sol['remaining_iol'] / mod['IO_Link_Ports'])
                total_modules.append((mod, needed))
                total_cost += mod['Precio'] * needed
                total_count += needed
                break

        # Evaluar si esta solución es mejor
        if (total_count < best_modules_count or
            (total_count == best_modules_count and total_cost < best_cost)):
            best_solution = total_modules
            best_cost = total_cost
            best_modules_count = total_count

    # Estrategia con módulos separados (como respaldo)
    separate_modules = []
    separate_cost = 0
    separate_count = 0

    # DI separados
    if di_needed > 0:
        di_mods = all_mods[all_mods['Entradas_DI'] > 0]
        if not di_mods.empty:
            best_di = di_mods.iloc[0]
            needed = ceil(di_needed / best_di['Entradas_DI'])
            separate_modules.append((best_di, needed))
            separate_cost += best_di['Precio'] * needed
            separate_count += needed

    # DO separados
    if do_needed > 0:
        do_mods = all_mods[all_mods['Salidas_DO'] > 0]
        if not do_mods.empty:
            best_do = do_mods.iloc[0]
            needed = ceil(do_needed / best_do['Salidas_DO'])
            separate_modules.append((best_do, needed))
            separate_cost += best_do['Precio'] * needed
            separate_count += needed

    # IO-Link separados
    if iol_needed > 0:
        iol_mods = all_mods[all_mods['IO_Link_Ports'] > 0]
        if not iol_mods.empty:
            best_iol = iol_mods.iloc[0]
            needed = ceil(iol_needed / best_iol['IO_Link_Ports'])
            separate_modules.append((best_iol, needed))
            separate_cost += best_iol['Precio'] * needed
            separate_count += needed

    # Comparar solución separada con la mejor mixta
    if (separate_count < best_modules_count or
        (separate_count == best_modules_count and separate_cost < best_cost)):
        best_solution = separate_modules
        best_cost = separate_cost
        best_modules_count = separate_count

    if best_solution is None:
        return [], 0, "No se encontraron módulos compatibles"

    # Verificar cobertura total
    total_di_covered = sum(mod['Entradas_DI'] * qty for mod, qty in best_solution)
    total_do_covered = sum(mod['Salidas_DO'] * qty for mod, qty in best_solution)
    total_iol_covered = sum(mod['IO_Link_Ports'] * qty for mod, qty in best_solution)

    # Verificar que la solución cubre los requerimientos
    if (total_di_covered < di_needed or
        total_do_covered < do_needed or
        total_iol_covered < iol_needed):
        return [], 0, f"No se puede cubrir los requerimientos (DI: {total_di_covered}/{di_needed}, DO: {total_do_covered}/{do_needed}, IO-Link: {total_iol_covered}/{iol_needed})"

    return best_solution, best_modules_count, None

def enumerate_solutions(req, df, fam_limits):
    """Enumera todas las soluciones posibles para cada familia considerando zonas individuales"""
    familias_disponibles = df["Familia"].unique()
    solutions = []
    rejected_families = []

    for fam in familias_disponibles:
        fam_df = df[df["Familia"] == fam]
        max_mods = fam_limits.get(fam, 9)

        rejection_reason = None

        # Buscar módulo base - si no hay, crear uno virtual
        base = fam_df[fam_df["Tipo"].str.lower() == "base"]
        if base.empty:
            base_price = 200.0
            base_ref = f"{fam}-CPU-BASE"
        else:
            base = base.sort_values("Precio").iloc[0]
            base_price = base["Precio"]
            base_ref = base["Referencia"]

        # Calcular módulos necesarios para cada zona
        zone_modules = []
        total_modules_needed = 0

        for zone in req['zones']:
            zone_id = zone['zone_id']
            di_needed = zone['digital_inputs']
            do_needed = zone['digital_outputs']
            iol_needed = zone['io_link_sensors']

            # Calcular módulos para esta zona
            zone_solution, zone_modules_count, zone_error = calculate_zone_modules(
                fam_df, di_needed, do_needed, iol_needed
            )

            if zone_error:
                rejection_reason = f"Zona {zone_id}: {zone_error}"
                break

            zone_modules.append({
                'zone_id': zone_id,
                'modules': zone_solution,
                'modules_count': zone_modules_count
            })
            total_modules_needed += zone_modules_count

        if rejection_reason:
            rejected_families.append({
                "Familia": fam,
                "Razon": rejection_reason,
                "Modulos_necesarios": total_modules_needed,
                "Limite_familia": max_mods
            })
            continue

        # Verificar si excede el límite total de módulos
        if total_modules_needed > max_mods:
            rejection_reason = f"Excede el límite de módulos ({total_modules_needed} > {max_mods})"
            rejected_families.append({
                "Familia": fam,
                "Razon": rejection_reason,
                "Modulos_necesarios": total_modules_needed,
                "Limite_familia": max_mods
            })
            continue

        # Calcular precio total y componentes
        price = base_price
        components = [(base_ref, 1)]

        # Agregar módulos de todas las zonas
        module_totals = {}

        for zone_data in zone_modules:
            for mod, qty in zone_data['modules']:
                ref = mod['Referencia']
                if ref in module_totals:
                    module_totals[ref]['quantity'] += qty
                else:
                    module_totals[ref] = {
                        'module': mod,
                        'quantity': qty
                    }

        # Agregar al precio y componentes
        for ref, data in module_totals.items():
            mod = data['module']
            qty = data['quantity']
            components.append((ref, qty))
            price += mod['Precio'] * qty

        solutions.append({
            "Familia": fam,
            "Precio_total": round(price, 2),
            "Componentes": components,
            "Modulos_totales": total_modules_needed,
            "Distribucion_zonas": zone_modules
        })

    solutions.sort(key=lambda s: s["Precio_total"])
    return solutions, rejected_families

def generate_solution_report(req, solution, protocol):
    """Genera un reporte detallado de la solución"""
    report_lines = []

    report_lines.append("=" * 60)
    report_lines.append("REPORTE DE SOLUCIÓN SMC")
    report_lines.append("=" * 60)
    report_lines.append("")

    # Información general
    report_lines.append("INFORMACIÓN GENERAL:")
    report_lines.append(f"  Familia: {solution['Familia']}")
    report_lines.append(f"  Protocolo: {protocol}")
    report_lines.append(f"  Precio Total: {solution['Precio_total']}€")
    report_lines.append(f"  Módulos Totales: {solution['Modulos_totales']}")
    report_lines.append("")

    # Configuración de zonas
    report_lines.append("CONFIGURACIÓN DE ZONAS:")
    report_lines.append(f"  Número de zonas: {req['num_zones']}")
    report_lines.append(f"  Distancia máxima: {req['distance_m']} m")
    report_lines.append("")

    for zone in req['zones']:
        zone_id = zone['zone_id']
        report_lines.append(f"  Zona {zone_id}:")
        report_lines.append(f"    - Entradas digitales: {zone['digital_inputs']}")
        report_lines.append(f"    - Salidas digitales: {zone['digital_outputs']}")
        report_lines.append(f"    - Sensores IO-Link: {zone['io_link_sensors']}")

    report_lines.append("")

    # Lista de componentes
    report_lines.append("LISTA DE COMPONENTES:")
    total_price = 0
    for ref, qty in solution['Componentes']:
        if ref.endswith("-CPU-BASE"):
            price = 200.0
        else:
            price = 0.0

        subtotal = price * qty
        total_price += subtotal
        report_lines.append(f"  {ref:<30} x{qty:>3} = {subtotal:>8.2f}€")

    report_lines.append("-" * 50)
    report_lines.append(f"{'TOTAL:':<37} {total_price:>8.2f}€")
    report_lines.append("")

    # Distribución por zonas
    if len(req['zones']) > 1:
        report_lines.append("DISTRIBUCIÓN POR ZONAS:")
        for zone_data in solution['Distribucion_zonas']:
            zone_id = zone_data['zone_id']
            zone_modules = zone_data['modules']
            zone_count = zone_data['modules_count']

            report_lines.append(f"  Zona {zone_id} ({zone_count} módulos):")
            for mod, qty in zone_modules:
                report_lines.append(f"    - {mod['Referencia']} x{qty}")

        report_lines.append("")

    # Pie de página
    report_lines.append("=" * 60)
    report_lines.append("Reporte generado por Calculador SMC")
    report_lines.append("=" * 60)

    return "\n".join(report_lines)

# Interfaz web principal
def main():
    if not check_password():
        return

    # Mostrar usuario actual
    st.sidebar.success(f"Conectado como: {st.session_state['current_user']}")
    if st.sidebar.button("Cerrar Sesión"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

    st.title("🔧 Calculador de Soluciones SMC")
    st.markdown("**Calculador de módulos SMC con configuración por zonas**")

    # Subida de archivos
    st.header("1. Cargar Archivos de Configuración")

    col1, col2 = st.columns(2)

    with col1:
        catalog_file = st.file_uploader(
            "Catálogo de Módulos (Configs.xlsx)",
            type=['xlsx', 'xls'],
            help="Archivo con la información de los módulos SMC"
        )

    with col2:
        families_file = st.file_uploader(
            "Configuración de Familias (Familias.xlsx)",
            type=['xlsx', 'xls'],
            help="Archivo con los límites y protocolos de las familias"
        )

    if catalog_file and families_file:
        try:
            # Cargar archivos
            catalog_df = pd.read_excel(catalog_file, sheet_name=0)
            families_df = pd.read_excel(families_file, sheet_name=0)

            # Procesar datos
            df, fam_limits, fam_protocols = load_catalog_with_limits_web(catalog_df, families_df)

            st.success(f"✅ Archivos cargados correctamente: {len(df)} módulos, {len(fam_limits)} familias")

            # Selección de protocolo
            st.header("2. Seleccionar Protocolo de Comunicación")

            all_protocols = set()
            for protocols in fam_protocols.values():
                all_protocols.update(protocols)

            selected_protocol = st.selectbox(
                "Protocolo de comunicación:",
                sorted(list(all_protocols)),
                help="Selecciona el protocolo que necesitas"
            )

            # Filtrar por protocolo
            df, fam_limits, compatible_families = filter_families_by_protocol(
                df, fam_limits, fam_protocols, selected_protocol
            )

            if df.empty:
                st.error("❌ No hay módulos compatibles con el protocolo seleccionado")
                return

            st.info(f"✅ Familias compatibles: {', '.join(compatible_families)}")

            # Configuración de zonas
            st.header("3. Configuración de Zonas")

            num_zones = st.number_input("Número de zonas:", min_value=1, max_value=20, value=1)
            zones_equal = st.checkbox("¿Todas las zonas son iguales?")

            zones = []

            if zones_equal:
                st.subheader("Configuración para todas las zonas (iguales)")
                col1, col2, col3 = st.columns(3)

                with col1:
                    di = st.number_input("Entradas digitales:", min_value=0, value=0, key="di_all")
                with col2:
                    do = st.number_input("Salidas digitales:", min_value=0, value=0, key="do_all")
                with col3:
                    iol = st.number_input("Sensores IO-Link:", min_value=0, value=0, key="iol_all")

                for i in range(num_zones):
                    zones.append({
                        'zone_id': i + 1,
                        'digital_inputs': di,
                        'digital_outputs': do,
                        'io_link_sensors': iol
                    })

            else:
                st.subheader("Configuración individual por zona")

                for i in range(num_zones):
                    st.write(f"**Zona {i+1}**")
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        di = st.number_input("DI:", min_value=0, value=0, key=f"di_{i}")
                    with col2:
                        do = st.number_input("DO:", min_value=0, value=0, key=f"do_{i}")
                    with col3:
                        iol = st.number_input("IO-Link:", min_value=0, value=0, key=f"iol_{i}")

                    zones.append({
                        'zone_id': i + 1,
                        'digital_inputs': di,
                        'digital_outputs': do,
                        'io_link_sensors': iol
                    })

            # Parámetros adicionales
            st.header("4. Parámetros Adicionales")

            col1, col2 = st.columns(2)
            with col1:
                distance_m = st.number_input("Distancia máxima entre zonas (m):", min_value=0.0, value=10.0)
            with col2:
                connector_type = st.selectbox(
                    "Tipo de conector:",
                    ["", "M8", "M12", "mixto"],
                    help="Deja vacío si es indiferente"
                )

            # Preparar requerimientos
            req = {
                "zones": zones,
                "num_zones": num_zones,
                "zones_equal": zones_equal,
                "distance_m": distance_m,
                "connector_type": connector_type,
                "total_digital_inputs": sum(zone['digital_inputs'] for zone in zones),
                "total_digital_outputs": sum(zone['digital_outputs'] for zone in zones),
                "total_io_link_sensors": sum(zone['io_link_sensors'] for zone in zones),
            }

            req["total_inputs"] = req["total_digital_inputs"] + req["total_io_link_sensors"]
            req["total_outputs"] = req["total_digital_outputs"]

            # Mostrar resumen
            st.header("5. Resumen de Configuración")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Configuración de Zonas:**")
                st.write(f"- Número de zonas: {req['num_zones']}")
                st.write(f"- Zonas iguales: {'Sí' if req['zones_equal'] else 'No'}")
                st.write(f"- Distancia máxima: {req['distance_m']} m")
                if connector_type:
                    st.write(f"- Tipo de conector: {connector_type}")

            with col2:
                st.write("**Totales:**")
                st.write(f"- Entradas digitales: {req['total_digital_inputs']}")
                st.write(f"- Salidas digitales: {req['total_digital_outputs']}")
                st.write(f"- Sensores IO-Link: {req['total_io_link_sensors']}")

            # Detalles por zona si hay más de una
            if req['num_zones'] > 1:
                st.write("**Detalle por zona:**")
                zone_data = []
                for zone in zones:
                    zone_data.append({
                        "Zona": zone['zone_id'],
                        "DI": zone['digital_inputs'],
                        "DO": zone['digital_outputs'],
                        "IO-Link": zone['io_link_sensors']
                    })
                st.dataframe(pd.DataFrame(zone_data), hide_index=True)

            # Botón para calcular
            if st.button("🔍 Calcular Soluciones", type="primary"):
                # Verificar que hay algo que calcular
                if req["total_inputs"] == 0 and req["total_outputs"] == 0:
                    st.warning("⚠️ Debes especificar al menos una entrada o salida para calcular")
                    return

                with st.spinner("Calculando soluciones..."):
                    # Enumerar soluciones
                    solutions, rejected_families = enumerate_solutions(req, df, fam_limits)

                    if not solutions:
                        st.error("❌ No se encontraron soluciones válidas")
                        
                        if rejected_families:
                            st.subheader("Familias descartadas:")
                            for rejection in rejected_families:
                                st.write(f"- **{rejection['Familia']}**: {rejection['Razon']}")
                        return

                    # Mostrar resultados
                    st.header("6. Soluciones Encontradas")
                    st.success(f"✅ Se encontraron {len(solutions)} solución(es)")

                    # Mostrar las mejores 3 soluciones
                    for i, sol in enumerate(solutions[:3]):
                        with st.expander(f"Solución {i+1}: {sol['Familia']} - {sol['Precio_total']}€", expanded=(i==0)):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write("**Información General:**")
                                st.write(f"- Familia: {sol['Familia']}")
                                st.write(f"- Precio Total: {sol['Precio_total']}€")
                                st.write(f"- Módulos Totales: {sol['Modulos_totales']}")
                                st.write(f"- Protocolo: {selected_protocol}")

                            with col2:
                                st.write("**Componentes:**")
                                for ref, qty in sol['Componentes']:
                                    st.write(f"- {ref} x{qty}")

                            # Distribución por zonas si hay más de una
                            if req['num_zones'] > 1:
                                st.write("**Distribución por zonas:**")
                                for zone_data in sol['Distribucion_zonas']:
                                    zone_id = zone_data['zone_id']
                                    zone_modules = zone_data['modules']
                                    zone_count = zone_data['modules_count']
                                    
                                    st.write(f"Zona {zone_id} ({zone_count} módulos):")
                                    for mod, qty in zone_modules:
                                        st.write(f"  - {mod['Referencia']} x{qty}")

                            # Botón para generar reporte
                            if st.button(f"📄 Generar Reporte", key=f"report_{i}"):
                                report = generate_solution_report(req, sol, selected_protocol)
                                
                                # Crear archivo de descarga
                                report_bytes = report.encode('utf-8')
                                filename = f"smc_solution_{sol['Familia'].lower()}_{int(sol['Precio_total'])}.txt"
                                
                                st.download_button(
                                    label="💾 Descargar Reporte",
                                    data=report_bytes,
                                    file_name=filename,
                                    mime="text/plain",
                                    key=f"download_{i}"
                                )

                    # Mostrar familias rechazadas si las hay
                    if rejected_families:
                        st.subheader("Familias descartadas:")
                        rejected_df = pd.DataFrame(rejected_families)
                        st.dataframe(rejected_df, hide_index=True)

        except Exception as e:
            st.error(f"❌ Error al procesar los archivos: {str(e)}")
            st.write("Por favor, verifica que los archivos tienen el formato correcto.")

    else:
        st.info("👆 Por favor, carga ambos archivos (Catálogo de Módulos y Configuración de Familias) para continuar.")

# Ejecutar la aplicación
if __name__ == "__main__":
    main()
       