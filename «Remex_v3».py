import os
import numpy as np
import tkinter as tk
import rasterio
from rasterio.mask import mask
from rasterio.features import rasterize
import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.colors import LinearSegmentedColormap
import pyodbc
import warnings
import xarray as xr
from rasterio.features import shapes
from shapely.geometry import shape
from shapely.ops import unary_union

warnings.filterwarnings("ignore")

# Налаштування графіки
plt.style.use('default')
mpl.rcParams['path.simplify'] = True
mpl.rcParams['path.simplify_threshold'] = 1.0
mpl.rcParams['lines.antialiased'] = True
mpl.rcParams['patch.antialiased'] = True

# --- Словник перекладів (Українська / English) ---
current_lang = "UA"

LANG_DATA = {
    "UA": {
        "title": "Remex_v3 - Моделювання розливу",
        "right_header": "РОЗРАХУНКИ КІНЦЕВОГО КОЕФІЦІЄНТУ\nЕФЕКТИВНОСТІ",
        "lbl_lang": "Мова / Language:",
        "sec_layers": "ШАРИ",
        "chk_height": "Рельєф",
        "chk_soil": "Тип ґрунту",
        "chk_rivers": "Річки",
        "sec_local": "ЛОКАЛЬНИЙ СТАН",
        "lbl_coords": "координати:",
        "lbl_lat": "Ш:",
        "lbl_lon": "Д:",
        "lbl_max_conc": "max концентрація:",
        "unit_mg_kg": "мг/кг",
        "lbl_volume": "загальний об'єм:",
        "unit_tons": "т",
        "lbl_river_mass": "із них у водоймі:",
        "lbl_area": "площа забруднення:",
        "unit_km2": "км²",
        "lbl_intensity": "відносна інтенс.:",
        "sec_cleaning": "ОЧИЩЕННЯ ГРУНТУ",
        "lbl_clean_type": "вид очищення:",
        "sec_climate": "КЛІМАТИЧНІ УМОВИ",
        "odd_warn": "Оберіть парну кількість місяців!",
        "tb_month": "Місяць",
        "tb_temp": "T(°)",
        "tb_hum": "Волог.(%)",
        "tb_precip": "Опади(мм)",
        "bio_warn": "Ризикові умови для біоагентів,\nризик низької ефективності.",
        "btn_update": "ОНОВИТИ ДАНІ",
        "btn_clear": "ОЧИСТИТИ ДАНІ",
        "lbl_timeline": "хронологія процесу",
        "clean_soil": "чистий ґрунт",
        "unknown": "невідомо",
        "out_bounds": "поза межами",
        "unit_m": " м",
        "unit_km": " км",
        "clean_options": [
            "Без біоагентів", "Сорго + ґр. бактерії", "Без рослин + ґр. бактерії",
            "Просо + ґр. бактерії", "Ґр. бактерії", "Суміш + ґр. бактерії",
            "Сорго", "Суміш", "Просо"
        ],
        "months": ["Січ.", "Лют.", "Бер.", "Квіт.", "Трав.", "Черв.", "Лип.", "Серп.", "Вер.", "Жовт.", "Лист.", "Груд."],
        "wrb": {
            "CH": "Чорноземи", "KS": "Каштанові", "FL": "Алювіальні", "HS": "Болотні", 
            "GL": "Лучно-глейові", "ST": "Стагноглейові", "AR": "Піщані", "LP": "Скелетні", 
            "CM": "Буроземи", "LV": "Підзолисті", "PH": "Лучно-чорноземні", "AN": "Вулканічні", 
            "AL": "Лесовані", "LX": "Глинисто-ілювіальні", "FR": "Червоноземи", "CL": "Карбонатні", 
            "CR": "Мерзлотні", "RT": "Дерново-підзолисті", "WR": "Водні поверхні"
        },
        "txt_soil_type": "Тип ґрунту: ",
        "txt_kg_bak": "K_G (бактерії) = ",
        "txt_kg_rosl": "K_G (рослини)  = ",
        "txt_summary": "ПІДСУМОК\n",
        "txt_cycles": "Кількість циклів по 2 міс.: ",
        "txt_avg_kb": "Середній K_бак = ",
        "txt_avg_kr": "Середній K_росл = ",
        "txt_avg_kp": "СЕРЕДНІЙ K_прир = ",
        "txt_eff_lab": "Ефективність (E_лаб) = ",
        "txt_final_formula": "Кінцевий коеф. = K_прир × E_лаб\n",
        "txt_no_data": "Відсутні або некоректні дані.",
        "txt_select_months": "Оберіть місяці для розрахунку."
    },
    "EN": {
        "title": "Remex_v3 - Oil Spill Simulation",
        "right_header": "FINAL EFFICIENCY\nCOEFFICIENT CALCULATIONS",
        "lbl_lang": "Language / Мова:",
        "sec_layers": "LAYERS",
        "chk_height": "Terrain",
        "chk_soil": "Soil type",
        "chk_rivers": "Rivers",
        "sec_local": "SITE STATUS",
        "lbl_coords": "coordinates:",
        "lbl_lat": "Lat:",
        "lbl_lon": "Lon:",
        "lbl_max_conc": "Max concentration:",
        "unit_mg_kg": "mg/kg",
        "lbl_volume": "Total volume:",
        "unit_tons": "t",
        "lbl_river_mass": "In water body:",
        "lbl_area": "contamination area:",
        "unit_km2": "km²",
        "lbl_intensity": "relative intensity:",
        "sec_cleaning": "SOIL REMEDIATION",
        "lbl_clean_type": "remediation type:",
        "sec_climate": "CLIMATE CONDITIONS",
        "odd_warn": "Select an even number of months!",
        "tb_month": "Month",
        "tb_temp": "T(°)",
        "tb_hum": "Hum.(%)",
        "tb_precip": "Precip.(mm)",
        "bio_warn": "Risky conditions for bioagents,\nrisk of low efficiency.",
        "btn_update": "UPDATE DATA",
        "btn_clear": "CLEAR DATA",
        "lbl_timeline": "process timeline",
        "clean_soil": "clean soil",
        "unknown": "unknown",
        "out_bounds": "out of bounds",
        "unit_m": " m",
        "unit_km": " km",
        "clean_options": [
            "No bioagents", "Sorghum + soil bacteria", "No plants + soil bacteria",
            "Millet + soil bacteria", "Soil bacteria", "Mix + soil bacteria",
            "Sorghum", "Mix", "Millet"
        ],
        "months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "wrb": {
            "CH": "Chernozems", "KS": "Kastanozems", "FL": "Fluvisols", "HS": "Histosols", 
            "GL": "Gleysols", "ST": "Stagnosols", "AR": "Arenosols", "LP": "Leptosols", 
            "CM": "Cambisols", "LV": "Luvisols", "PH": "Phaeozems", "AN": "Andosols", 
            "AL": "Alisols", "LX": "Lixisols", "FR": "Ferralsols", "CL": "Calcisols", 
            "CR": "Cryosols", "RT": "Retisols", "WR": "Water bodies"
        },
        "txt_soil_type": "Soil type: ",
        "txt_kg_bak": "K_G (bacteria) = ",
        "txt_kg_rosl": "K_G (plants)   = ",
        "txt_summary": "SUMMARY\n",
        "txt_cycles": "Number of 2-month cycles: ",
        "txt_avg_kb": "Average K_bac = ",
        "txt_avg_kr": "Average K_plant = ",
        "txt_avg_kp": "AVERAGE K_nat = ",
        "txt_eff_lab": "Efficiency (E_lab) = ",
        "txt_final_formula": "Final coeff. = K_nat × E_lab\n",
        "txt_no_data": "Missing or incorrect data.",
        "txt_select_months": "Select months for calculation."
    }
}

def normalize_wrb(value):
    if not value: return None
    v = str(value).strip()
    if len(v) == 2 and v.isalpha(): return v.upper()
    v_low = v.lower()
    mapping = {
        "retisols": "RT", "stagnosols": "ST", "chernozems": "CH", "phaeozems": "PH",
        "luvisols": "LV", "cambisols": "CM", "gleysols": "GL", "fluvisols": "FL",
        "arenosols": "AR", "leptosols": "LP", "kastanozems": "KS", "histosols": "HS",
        "andosols": "AN", "alisols": "AL", "lixisols": "LX", "ferralsols": "FR",
        "calcisols": "CL", "cryosols": "CR"
    }
    return mapping.get(v_low)

# --- Шляхи до файлів ---
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    script_dir = os.getcwd()

BASE_DIR = os.path.join(script_dir, "data")

if not os.path.exists(BASE_DIR):
    BASE_DIR = r"C:\Users\Admin\Documents\Pusha\Проєкти_2026-2027\Oil_Spill_Project\Remex_v3\data"

print("Завантаження кордонів...")
border = gpd.read_file(os.path.join(BASE_DIR, "gadm41_UKR_shp", "gadm41_UKR_0.shp"))

print("Завантаження DEM...")
dem_path = os.path.join(BASE_DIR, "ukrain_dem_optimized.tif")
with rasterio.open(dem_path) as src:
    crs = src.crs
    border = border.to_crs(crs)
    dem_data, dem_transform = mask(src, border.geometry, crop=True, nodata=np.nan)
    dem = dem_data[0][::10, ::10].astype(np.float32)
    dem_transform = dem_transform * rasterio.Affine.scale(10, 10)

print("Завантаження ґрунтів...")
soil_path = os.path.join(BASE_DIR, "HWSD_RASTER", "hwsd.bil")
with rasterio.open(soil_path) as src:
    soil_data, soil_transform = mask(src, border.geometry, crop=True, nodata=src.nodata)
    soil = soil_data[0][::4, ::4].astype(np.int32)
    if src.nodata is not None: soil[soil == src.nodata] = 0
    soil_transform = soil_transform * rasterio.Affine.scale(4, 4)

print("Завантаження річок...")
rivers = gpd.read_file(os.path.join(BASE_DIR, "rivers_optimized.gpkg"), layer="river_map_clipped").to_crs(crs)
is_geo = hasattr(crs, "is_geographic") and crs.is_geographic
if is_geo:
    pixel_size_m = abs(dem_transform.a) * 111320.0
else:
    pixel_size_m = abs(dem_transform.a)

rivers_projected = rivers.to_crs(epsg=3857)
buffered_projected = rivers_projected.geometry.buffer(pixel_size_m * 0.5)
buffered_rivers = buffered_projected.to_crs(crs)

river_shapes = [(geom, 1) for geom in buffered_rivers if geom is not None]
if river_shapes:
    river_mask = rasterize(river_shapes, out_shape=dem.shape, transform=dem_transform, fill=0, dtype=np.uint8)
else:
    river_mask = np.zeros(dem.shape, dtype=np.uint8)

tol = 0.03 if is_geo else 3000
border_plot = border.geometry.simplify(tol, preserve_topology=False)
rivers_plot = rivers.geometry.simplify(tol, preserve_topology=False)

dem_inv_transform = ~dem_transform
soil_inv_transform = ~soil_transform

print("Підключення до бази HWSD2...")
db_path = os.path.join(BASE_DIR, "HWSD2_DB", "HWSD2.mdb")

wrb_coefficients = {
    "CH": (0.8, 0.020), "KS": (0.6, 0.015), "FL": (0.4, 0.015), "HS": (1.6, 0.045), 
    "GL": (0.7, 0.010), "ST": (0.6, 0.010), "AR": (0.2, 0.035), "LP": (0.1, 0.005), 
    "CM": (0.5, 0.012), "LV": (0.5, 0.012), "PH": (0.7, 0.018), "AN": (0.9, 0.030), 
    "AL": (0.5, 0.012), "LX": (0.5, 0.012), "FR": (0.5, 0.012), "CL": (0.4, 0.010), 
    "CR": (0.1, 0.002), "RT": (0.5, 0.012), "WR": (0.0, 0.000)
}

soil_ph_k = {
    "PH": 0.95, "CH": 0.90, "GL": 0.90, "LV": 0.80, "AN": 0.80,
    "KS": 0.80, "CM": 0.70, "LX": 0.70, "CL": 0.70, "AR": 0.55,
    "ST": 0.40, "HS": 0.15, "RT": 0.15, "FR": 0.08, "AL": 0.04,
    "FL": 0.50, "LP": 0.50, "CR": 0.50, "WR": 0.00
}

soil_k_sorghum = {
    "CH": 1.00, "KS": 1.00, "CL": 1.00, "FL": 1.00,
    "PH": 0.98, "GL": 0.89, "LV": 0.80, "AN": 0.80,
    "CM": 0.71, "LX": 0.71, "AR": 0.63, "ST": 0.54,
    "RT": 0.36, "HS": 0.36, "FR": 0.27, "AL": 0.18,
    "LP": 0.50, "CR": 0.50, "WR": 0.00
}

soil_k_millet = {
    "LX": 1.00, "LV": 1.00, "AN": 1.00, "GL": 1.00,
    "CM": 1.00, "AR": 1.00, "ST": 1.00, "PH": 0.88,
    "RT": 0.75, "HS": 0.75, "FR": 0.63, "CH": 0.50,
    "AL": 0.50, "KS": 0.38, "CL": 0.25,
    "FL": 1.00, "LP": 0.50, "CR": 0.50, "WR": 0.00
}

smu_to_wrb = {}
smu_to_capacity = {0: 0.5}
smu_to_rate = {0: 0.01}

try:
    conn = pyodbc.connect(rf"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_path};")
    cur = conn.cursor()
    cur.execute("SELECT * FROM HWSD2_SMU")
    rows = cur.fetchall()
    for r in rows:
        if r[3] and r[8]:
            wrb_n = normalize_wrb(r[8])
            if wrb_n: 
                smu_to_wrb[int(r[3])] = wrb_n
                cap, rat = wrb_coefficients.get(wrb_n, (0.5, 0.01))
                smu_to_capacity[int(r[3])] = cap
                smu_to_rate[int(r[3])] = rat
    conn.close()
except Exception as e:
    print(f"Проблема з базою HWSD2: {e}")

print("Обробка кліматичних даних з ваговими коефіцієнтами (NetCDF)...")
climate_nc_path = os.path.join(BASE_DIR, "ukr_climate_1986_2026.nc")
monthly_t2m = None
monthly_d2m = None
monthly_tp = None

try:
    climate_ds = xr.open_dataset(climate_nc_path)
    
    years = climate_ds['valid_time.dt.year'].values
    min_year, max_year = np.min(years), np.max(years)
    if max_year > min_year:
        weights = 0.05 + 0.95 * (years - min_year) / (max_year - min_year)
    else:
        weights = np.ones_like(years, dtype=np.float32)

    months = climate_ds['valid_time.dt.month'].values
    monthly_t2m_list, monthly_d2m_list, monthly_tp_list = [], [], []

    for m in range(1, 13):
        m_mask = (months == m)
        m_weights = weights[m_mask]
        
        sub_t2m = climate_ds['t2m'].isel(valid_time=m_mask)
        sub_d2m = climate_ds['d2m'].isel(valid_time=m_mask)
        sub_tp = climate_ds['tp'].isel(valid_time=m_mask)

        w_da = xr.DataArray(m_weights, dims=['valid_time'], coords={'valid_time': sub_t2m.valid_time})
        
        t2m_m = (sub_t2m * w_da).sum(dim='valid_time') / w_da.sum()
        d2m_m = (sub_d2m * w_da).sum(dim='valid_time') / w_da.sum()
        tp_m = (sub_tp * w_da).sum(dim='valid_time') / w_da.sum()

        monthly_t2m_list.append(t2m_m)
        monthly_d2m_list.append(d2m_m)
        monthly_tp_list.append(tp_m)

    monthly_t2m = xr.concat(monthly_t2m_list, dim='month').compute()
    monthly_d2m = xr.concat(monthly_d2m_list, dim='month').compute()
    monthly_tp = xr.concat(monthly_tp_list, dim='month').compute()

except Exception as e:
    print(f"Кліматичні дані не завантажено: {e}")

xs, ys = dem_transform.c, dem_transform.f
extent = [xs, xs + dem_transform.a * dem.shape[1], ys + dem_transform.e * dem.shape[0], ys]

# Глобальні змінні стану
spill_lon, spill_lat = None, None
pan_last_x, pan_last_y = 0, 0
is_panning = False
is_animating = False 
is_spreading = False
spread_state = {}
spread_job = None

geo_aspect = 1.0 / np.cos(np.radians(49.0)) if is_geo else 1.0
spill_array = np.zeros(dem.shape, dtype=np.float32)
river_spill_array = np.zeros(dem.shape, dtype=np.float32)
river_spill_artists = []  

get_capacity_vec = np.vectorize(lambda smu: smu_to_capacity.get(smu, 0.5))
get_rate_vec = np.vectorize(lambda smu: smu_to_rate.get(smu, 0.01))
get_kg_vec = np.vectorize(lambda smu: soil_ph_k.get(smu_to_wrb.get(smu, ""), 0.5))
get_kg_sorghum_vec = np.vectorize(lambda smu: soil_k_sorghum.get(smu_to_wrb.get(smu, ""), 0.5))
get_kg_millet_vec = np.vectorize(lambda smu: soil_k_millet.get(smu_to_wrb.get(smu, ""), 0.5))

timeline_value = 0.0
month_vars = []

biorem_coefficients_by_index = {
    0: 0.500, 1: 0.750, 2: 0.917, 3: 0.917, 
    4: 0.917, 5: 0.750, 6: 0.583, 7: 0.500, 8: 0.417
}

sim_cache = {
    'params': None,
    'r_min': 0, 'r_max': 0, 'c_min': 0, 'c_max': 0,
    'base_spill_intensity': None,
    'base_river_intensity': None,
    'base_total_river_mass': 0.0,
    'local_river_mask': None,
    'pixel_area_m2': 0,
    'window_soil_ids': None
}

update_job = None

def schedule_update(*args):
    global update_job
    if update_job is not None:
        root.after_cancel(update_job)
    update_job = root.after(400, request_update)

def btn_update_data_click():
    request_update()

def get_height_and_soil(x, y):
    L = LANG_DATA[current_lang]
    c, r = dem_inv_transform * (x, y)
    r, c = int(round(r)), int(round(c))
    if 0 <= r < dem.shape[0] and 0 <= c < dem.shape[1]:
        h_txt = f"{dem[r, c]:.0f}{L['unit_m']}" if not np.isnan(dem[r, c]) else L["unknown"]
    else:
        h_txt = L["out_bounds"]
        
    sc, sr = soil_inv_transform * (x, y)
    sr, sc = int(round(sr)), int(round(sc))
    if 0 <= sr < soil.shape[0] and 0 <= sc < soil.shape[1]:
        wrb = smu_to_wrb.get(int(soil[sr, sc]))
        s_txt = L["wrb"].get(wrb, L["unknown"])
    else:
        s_txt = L["out_bounds"]
    return h_txt, s_txt

def clear_data():
    global spill_lon, spill_lat, river_spill_artists, timeline_value, current_year, climate_data_by_year, is_animating, is_spreading, spread_job
    L = LANG_DATA[current_lang]
    
    if spread_job is not None:
        root.after_cancel(spread_job)
        spread_job = None
        
    is_animating = False
    is_spreading = False
    spill_lon, spill_lat = None, None
    coord_lon_var.set("")
    coord_lat_var.set("")
    max_conc.set(622.4) 
    volume_var.set(1000.0)
    
    sim_cache['params'] = None
    sim_cache['base_spill_intensity'] = None
    sim_cache['window_soil_ids'] = None
    
    area_label.config(text="0.0000")
    river_mass_label.config(text="0.00")
    intensity_label.config(text=f"0.00 {L['unit_mg_kg']}")
    height_label.config(text=f"— {L['unit_m'].strip()}")
    soil_label.config(text="—")

    calc_text.config(state=tk.NORMAL)
    calc_text.delete(1.0, tk.END)
    calc_text.config(state=tk.DISABLED)
    warn_frame.pack_forget()
    if 'odd_months_warn_lbl' in globals():
        odd_months_warn_lbl.pack_forget()
    
    spill_array.fill(0)
    river_spill_array.fill(0)
    spill_img.set_data(spill_array)
    
    for artist in river_spill_artists:
        try: artist.remove()
        except: pass
    river_spill_artists = []

    spill_marker.set_data([], [])
    clean_var.set(L["clean_options"][0])

    timeline_value = 0.0
    climate_data_by_year.clear()
    current_year = 2026
    year_label.config(text=str(current_year))

    for i in range(12):
        month_vars[i][1].set(False)
        climate_entries[i]['T'].delete(0, tk.END)
        climate_entries[i]['H'].delete(0, tk.END)
        climate_entries[i]['P'].delete(0, tk.END)

    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])

    draw_timeline()
    canvas.draw()

# --- Табличні масиви інтерполяції ---
def get_K_T_bak(T):
    xp = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 37, 38, 39, 40, 41, 42, 43]
    fp = [0, 0.033, 0.066, 0.099, 0.132, 0.165, 0.198, 0.231, 0.264, 0.297, 0.33, 0.363, 0.396, 0.4375, 0.475, 0.5125, 0.55, 0.5875, 0.625, 0.6625, 0.7, 0.7375, 0.775, 0.8125, 0.85, 0.8875, 0.925, 0.9625, 1.0, 1.0, 0.8, 0.6, 0.4, 0.2, 0.0, 0.0]
    return float(np.interp(T, xp, fp, left=0.0, right=0.0))

def get_K_W_bak(RH):
    xp = [0, 74, 75, 100]
    fp = [0.0, 0.0, 0.3, 1.0] 
    return float(np.interp(RH, xp, fp, left=0.0, right=1.0))

def get_K_T_sorghum(T):
    xp = [0, 7, 8, 9, 10, 11, 12, 13, 14, 15, 20, 25, 27, 32, 33, 34, 35, 36, 37, 38, 39, 40]
    fp = [0, 0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.88, 0.97, 1.0, 1.0, 0.88, 0.75, 0.63, 0.5, 0.38, 0.25, 0.13, 0.0]
    return float(np.interp(T, xp, fp, left=0.0, right=0.0))

def get_K_W_sorghum(RH):
    xp = [0, 10, 20, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100]
    fp = [0, 0.33, 0.67, 1.0, 0.99, 0.98, 0.97, 0.96, 0.95, 0.94, 0.93, 0.92, 0.91, 0.91, 0.90, 0.89, 0.88, 0.87, 0.86, 0.85, 0.84, 0.83, 0.82, 0.81, 0.80, 0.79, 0.78, 0.77, 0.76, 0.75, 0.74, 0.73, 0.72, 0.72, 0.73, 0.74, 0.74, 0.75, 0.76, 0.77, 0.78, 0.78, 0.79, 0.80, 0.81, 0.82, 0.83, 0.84, 0.85, 0.86, 0.87, 0.88, 0.89, 0.90, 0.91, 0.92, 0.93, 0.94, 0.95, 0.95, 0.96, 0.97, 0.98, 0.95, 0.87, 0.78, 0.70, 0.61, 0.53, 0.44, 0.36, 0.27, 0.19, 0.10]
    return float(np.interp(RH, xp, fp, left=0.0, right=0.10))

def get_K_P_sorghum(P):
    xp = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180]
    fp = [0, 0.08, 0.17, 0.25, 0.33, 0.42, 0.50, 0.57, 0.63, 0.70, 0.78, 0.86, 0.95, 1.0, 0.98, 0.95, 0.91, 0.86, 0.80]
    return float(np.interp(P, xp, fp, left=0.0, right=0.80))

def get_K_T_millet(T):
    xp = [-3.5, -2, 5, 10, 15, 20, 25, 30, 32, 35, 38, 40]
    fp = [0, 0.05, 0.1, 0.25, 0.5, 0.75, 1.0, 1.0, 0.94, 0.85, 0.76, 0.7]
    return float(np.interp(T, xp, fp, left=0.0, right=0.0))

def get_K_W_millet(RH):
    xp = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    fp = [0, 0.25, 0.5, 0.75, 1.0, 1.0, 1.0, 0.75, 0.5, 0.25, 0.0]
    return float(np.interp(RH, xp, fp, left=0.0, right=0.0))

def get_K_P_millet(P):
    xp = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 108, 110, 120, 130, 140, 150, 157.7]
    fp = [0, 0.093, 0.185, 0.278, 0.37, 0.463, 0.556, 0.648, 0.741, 0.833, 0.926, 1.0, 0.96, 0.759, 0.558, 0.356, 0.155, 0]
    return float(np.interp(P, xp, fp, left=0.0, right=0.0))

def request_update():
    global spill_lon, spill_lat, is_spreading
    if is_spreading: return
    
    try:
        val_lon = float(coord_lon_var.get())
        val_lat = float(coord_lat_var.get())
        spill_lon, spill_lat = val_lon, val_lat
        spill_marker.set_data([spill_lon], [spill_lat]) 
    except ValueError:
        pass

    if spill_lon is None or spill_lat is None: return
    
    max_c = float(max_conc.get())
    vol_tons = float(volume_var.get())
    current_params = (spill_lon, spill_lat, vol_tons, max_c)
    
    if sim_cache['params'] != current_params or sim_cache['base_spill_intensity'] is None:
        start_spill_simulation(current_params)
    else:
        apply_remediation_and_draw()

def start_spill_simulation(current_params):
    global is_spreading, spread_state, spread_job, river_spill_artists, timeline_value
    
    if spread_job is not None:
        root.after_cancel(spread_job)
        spread_job = None
        
    calc_text.config(state=tk.NORMAL)
    calc_text.delete(1.0, tk.END)
    calc_text.config(state=tk.DISABLED)
    warn_frame.pack_forget()

    spill_lon, spill_lat, vol_tons, max_c = current_params
    
    if max_c <= 0.0: return
    c_float, r_float = dem_inv_transform * (spill_lon, spill_lat)
    r_idx, c_idx = int(round(r_float)), int(round(c_float))
    
    if not (0 <= r_idx < dem.shape[0] and 0 <= c_idx < dem.shape[1]):
        sim_cache['params'] = current_params
        sim_cache['base_spill_intensity'] = None
        sim_cache['window_soil_ids'] = None
        apply_remediation_and_draw()
        return

    if is_geo:
        lat_rad = np.radians(spill_lat)
        px_m = abs(dem_transform.a) * 111320.0 * np.cos(lat_rad)
        py_m = abs(dem_transform.e) * 111320.0
        pixel_area_m2 = px_m * py_m
    else:
        px_m = abs(dem_transform.a)
        py_m = abs(dem_transform.e)
        pixel_area_m2 = px_m * py_m
    
    grad_x = 1.0 / px_m if px_m > 0 else 1.0
    grad_y = 1.0 / py_m if py_m > 0 else 1.0
    diag_g = np.sqrt(grad_x**2 + grad_y**2)
    
    W_factor = (vol_tons / max(max_c, 0.1))**0.4
    W = int(np.clip(25 + W_factor * 25, 40, 250))
    
    r_min, r_max = max(0, r_idx - W), min(dem.shape[0], r_idx + W + 1)
    c_min, c_max = max(0, c_idx - W), min(dem.shape[1], c_idx + W + 1)

    local_dem = dem[r_min:r_max, c_min:c_max].copy()
    local_river_mask = river_mask[r_min:r_max, c_min:c_max]
    
    valid_dem = local_dem[~np.isnan(local_dem)]
    if len(valid_dem) > 0:
        local_dem[np.isnan(local_dem)] = np.mean(valid_dem)
    else:
        local_dem.fill(0)

    r_ind = np.arange(r_min, r_max)
    c_ind = np.arange(c_min, c_max)
    C_mesh, R_mesh = np.meshgrid(c_ind, r_ind)
    X_coords = dem_transform.c + C_mesh * dem_transform.a + R_mesh * dem_transform.b
    Y_coords = dem_transform.f + C_mesh * dem_transform.a + R_mesh * dem_transform.e
    
    SC_mesh = np.clip(np.round(soil_inv_transform.c + X_coords * soil_inv_transform.a + Y_coords * soil_inv_transform.b).astype(np.int32), 0, soil.shape[1] - 1)
    SR_mesh = np.clip(np.round(soil_inv_transform.f + X_coords * soil_inv_transform.a + Y_coords * soil_inv_transform.e).astype(np.int32), 0, soil.shape[0] - 1)
    
    window_soil_ids = soil[SR_mesh, SC_mesh]
    local_capacity = get_capacity_vec(window_soil_ids).astype(np.float32)
    local_rate = get_rate_vec(window_soil_ids).astype(np.float32)

    soil_density_kg_m3 = 1300.0
    soil_depth_m = 0.2
    pixel_soil_mass_kg = pixel_area_m2 * soil_depth_m * soil_density_kg_m3
    user_max_tons_per_pixel = (max_c * pixel_soil_mass_kg) / 1e9

    effective_capacity_tons = np.where(local_river_mask == 1, 0.0, np.minimum((local_capacity * pixel_area_m2) / 1000.0, user_max_tons_per_pixel))

    local_oil = np.zeros_like(local_dem, dtype=np.float32)
    absorbed_oil = np.zeros_like(local_dem, dtype=np.float32)
    local_river_oil = np.zeros_like(local_dem, dtype=np.float32)
    local_r, local_c = r_idx - r_min, c_idx - c_min
    
    iterations = int(np.clip(250 + W_factor * 150, 300, 2000))
    oil_per_step = vol_tons / iterations  
    
    avg_temp = 15.0
    try:
        temps = [float(climate_entries[i]['T'].get()) for i in range(12) if climate_entries[i]['T'].get()]
        if temps: avg_temp = np.mean(temps)
    except ValueError:
        pass
        
    evap_rate = np.clip(0.0005 * (avg_temp + 10), 0.0001, 0.02)
    oil_density_kg_m3_liquid = 836.36  
    
    for artist in river_spill_artists:
        try: artist.remove()
        except: pass
    river_spill_artists = []
    
    timeline_value = 0.0
    draw_timeline()

    spread_state = {
        'current_step': 0, 'iterations': iterations, 'oil_per_step': oil_per_step,
        'local_oil': local_oil, 'absorbed_oil': absorbed_oil, 'local_river_oil': local_river_oil,
        'local_dem': local_dem, 'local_river_mask': local_river_mask,
        'effective_capacity_tons': effective_capacity_tons,
        'grad_x': grad_x, 'grad_y': grad_y, 'diag_g': diag_g,
        'pixel_area_m2': pixel_area_m2, 'oil_density_kg_m3_liquid': oil_density_kg_m3_liquid,
        'evap_rate': evap_rate, 'local_r': local_r, 'local_c': local_c,
        'r_min': r_min, 'r_max': r_max, 'c_min': c_min, 'c_max': c_max,
        'max_c': max_c, 'current_params': current_params,
        'pixel_soil_mass_kg': pixel_soil_mass_kg, 'window_soil_ids': window_soil_ids
    }
    
    is_spreading = True
    do_spill_step()

def do_spill_step():
    global is_spreading, spread_job
    if not is_spreading: return
    
    s = spread_state
    chunk_size = 40 
    
    for _ in range(chunk_size):
        if s['current_step'] >= s['iterations']: break
        
        s['local_oil'][s['local_r'], s['local_c']] += s['oil_per_step']
        s['local_oil'] -= s['local_oil'] * (s['evap_rate'] * 0.1) 
        
        H = s['local_dem'] + (s['local_oil'] * 1000.0) / (s['oil_density_kg_m3_liquid'] * s['pixel_area_m2'])
        H_c = H[1:-1, 1:-1]
        
        diffusion = 0.015
        
        d_N = np.maximum(0, H_c - H[:-2, 1:-1] + diffusion) * s['grad_y']
        d_S = np.maximum(0, H_c - H[2:, 1:-1] + diffusion) * s['grad_y']
        d_W = np.maximum(0, H_c - H[1:-1, :-2] + diffusion) * s['grad_x']
        d_E = np.maximum(0, H_c - H[1:-1, 2:] + diffusion) * s['grad_x']
        
        total_d = d_N + d_S + d_W + d_E + 1e-9
        moving = s['local_oil'][1:-1, 1:-1] * 0.95
        
        s['local_oil'][1:-1, 1:-1] -= moving
        s['local_oil'][:-2, 1:-1] += moving * (d_N / total_d)
        s['local_oil'][2:, 1:-1] += moving * (d_S / total_d)
        s['local_oil'][1:-1, :-2] += moving * (d_W / total_d)
        s['local_oil'][1:-1, 2:] += moving * (d_E / total_d)
        
        in_river = s['local_oil'] * s['local_river_mask']
        s['local_river_oil'] += in_river
        s['local_oil'] -= in_river
        
        can_absorb = np.maximum(0, s['effective_capacity_tons'] - s['absorbed_oil'])
        actual_absorb = np.minimum(s['local_oil'] * 0.1, can_absorb)
        s['absorbed_oil'] += actual_absorb
        s['local_oil'] -= actual_absorb
        s['current_step'] += 1

    # Візуалізація процесу розтікання в реальному часі з колірним градієнтом
    current_spill = (s['local_oil'] + s['absorbed_oil']) * 1e9 / s['pixel_soil_mass_kg']
    spill_array.fill(0)
    spill_array[s['r_min']:s['r_max'], s['c_min']:s['c_max']] = np.clip(current_spill, 0.0, s['max_c'])
    spill_img.set_data(spill_array)
    spill_img.set_clim(vmin=0, vmax=s['max_c'] if s['max_c'] > 1e-3 else 1.0)
    canvas.draw_idle()

    if s['current_step'] < s['iterations']:
        spread_job = root.after(10, do_spill_step)
    else:
        is_spreading = False
        finalize_spill_simulation()

def finalize_spill_simulation():
    s = spread_state
    
    total_river_mass_tons = np.sum(s['local_river_oil'])
    
    sim_cache['base_total_river_mass'] = total_river_mass_tons
    sim_cache['base_spill_intensity'] = (s['local_oil'] + s['absorbed_oil']) * 1e9 / s['pixel_soil_mass_kg']
    sim_cache['base_river_intensity'] = s['local_river_oil'] * 1e9 / s['pixel_soil_mass_kg']
    
    sim_cache['local_river_mask'] = s['local_river_mask']
    sim_cache['r_min'] = s['r_min']; sim_cache['r_max'] = s['r_max']
    sim_cache['c_min'] = s['c_min']; sim_cache['c_max'] = s['c_max']
    sim_cache['pixel_area_m2'] = s['pixel_area_m2']
    sim_cache['window_soil_ids'] = s['window_soil_ids']
    sim_cache['params'] = s['current_params']
    
    apply_remediation_and_draw()

def apply_remediation_and_draw():
    global river_spill_artists
    L = LANG_DATA[current_lang]
    
    def add_text(t, tags=None):
        if tags: calc_text.insert(tk.END, t, tags)
        else: calc_text.insert(tk.END, t)
            
    calc_text.config(state=tk.NORMAL)
    calc_text.delete(1.0, tk.END)

    if sim_cache['base_spill_intensity'] is not None:
        r_min, r_max = sim_cache['r_min'], sim_cache['r_max']
        c_min, c_max = sim_cache['c_min'], sim_cache['c_max']
        local_river_mask = sim_cache['local_river_mask']
        pixel_area_m2 = sim_cache['pixel_area_m2']
        window_soil_ids = sim_cache['window_soil_ids']
        max_c = sim_cache['params'][3]
        vol_tons = sim_cache['params'][2]

        active_months_indices = [i for i, (m, var) in enumerate(month_vars) if var.get()]
        active_months_count = len(active_months_indices)
        
        cycles_count = active_months_count / 2.0
        time_factor = timeline_value * max(0.001, cycles_count) if active_months_count > 0 else 0
        
        clean_method = clean_var.get()
        opts_ua = LANG_DATA["UA"]["clean_options"]
        opts_en = LANG_DATA["EN"]["clean_options"]
        clean_idx = 0
        if clean_method in opts_ua: clean_idx = opts_ua.index(clean_method)
        elif clean_method in opts_en: clean_idx = opts_en.index(clean_method)

        has_plants = clean_idx in [1, 3, 5, 6, 7, 8]
        is_sorghum = clean_idx in [1, 6]
        is_millet = clean_idx in [3, 8]
        is_mixture = clean_idx in [5, 7]

        if active_months_count > 0:
            KG_matrix_bak = get_kg_vec(window_soil_ids).astype(np.float32)
            KG_matrix_sorghum = get_kg_sorghum_vec(window_soil_ids).astype(np.float32)
            KG_matrix_millet = get_kg_millet_vec(window_soil_ids).astype(np.float32)
            
            if is_mixture:
                KG_matrix_rosl = (KG_matrix_sorghum + KG_matrix_millet) / 2.0
            elif is_millet:
                KG_matrix_rosl = KG_matrix_millet
            else:
                KG_matrix_rosl = KG_matrix_sorghum
                
            total_K_bak = np.zeros_like(KG_matrix_bak)
            total_K_rosl = np.zeros_like(KG_matrix_bak)
            total_K_pryr = np.zeros_like(KG_matrix_bak)
            valid_months = 0

            ui_k_bak_sum = 0.0
            ui_k_rosl_sum = 0.0
            ui_k_pryr_sum = 0.0

            try:
                sc, sr = soil_inv_transform * (spill_lon, spill_lat)
                center_smu = int(soil[int(round(sr)), int(round(sc))])
                wrb_name_code = smu_to_wrb.get(center_smu, "")
                center_KG_bak = soil_ph_k.get(wrb_name_code, 0.5)
                
                if is_mixture:
                    center_KG_rosl = (soil_k_sorghum.get(wrb_name_code, 0.5) + soil_k_millet.get(wrb_name_code, 0.5)) / 2.0
                elif is_millet:
                    center_KG_rosl = soil_k_millet.get(wrb_name_code, 0.5)
                else:
                    center_KG_rosl = soil_k_sorghum.get(wrb_name_code, 0.5)
                    
                wrb_name = L["wrb"].get(wrb_name_code, L["unknown"])
            except:
                center_KG_bak = 0.5
                center_KG_rosl = 0.5
                wrb_name = L["unknown"]
                
            add_text(f"{L['txt_soil_type']}{wrb_name}\n")
            add_text(f"{L['txt_kg_bak']}{center_KG_bak:.3f}\n")
            if has_plants:
                add_text(f"{L['txt_kg_rosl']}{center_KG_rosl:.3f}\n")
            add_text("\n")

            for i in active_months_indices:
                try:
                    t_str = climate_entries[i]['T'].get()
                    h_str = climate_entries[i]['H'].get()
                    p_str = climate_entries[i]['P'].get()
                    if t_str and h_str:
                        T = float(t_str)
                        RH = float(h_str)
                        P = float(p_str) if p_str else 0.0

                        K_T_b = get_K_T_bak(T)
                        K_W_b = get_K_W_bak(RH)
                        
                        K_bak_m = (K_T_b + K_W_b + KG_matrix_bak) / 3.0
                        total_K_bak += K_bak_m
                        
                        ui_kb = (K_T_b + K_W_b + center_KG_bak) / 3.0
                        ui_k_bak_sum += ui_kb
                        
                        add_text(f"[{L['months'][i]}]\n", "bold")
                        add_text(f"T={T}°C, W={RH}%, P={P}mm\n")
                        add_text(f"K_Tб: {K_T_b:.3f}, K_Wб: {K_W_b:.3f}\n")
                        
                        if has_plants:
                            if is_mixture:
                                K_T_r = (get_K_T_sorghum(T) + get_K_T_millet(T)) / 2.0
                                K_W_r = (get_K_W_sorghum(RH) + get_K_W_millet(RH)) / 2.0
                                K_P_r = (get_K_P_sorghum(P) + get_K_P_millet(P)) / 2.0
                            elif is_millet:
                                K_T_r = get_K_T_millet(T)
                                K_W_r = get_K_W_millet(RH)
                                K_P_r = get_K_P_millet(P)
                            else:
                                K_T_r = get_K_T_sorghum(T)
                                K_W_r = get_K_W_sorghum(RH)
                                K_P_r = get_K_P_sorghum(P)
                                
                            add_text(f"K_Tр: {K_T_r:.3f}, K_Wр: {K_W_r:.3f}, K_Pр: {K_P_r:.3f}\n")
                            
                            K_rosl_m = (K_T_r + K_W_r + K_P_r + KG_matrix_rosl) / 4.0
                            total_K_rosl += K_rosl_m
                            total_K_pryr += (K_bak_m + K_rosl_m) / 2.0
                            
                            ui_kr = (K_T_r + K_W_r + K_P_r + center_KG_rosl) / 4.0
                            ui_k_rosl_sum += ui_kr
                            ui_k_pryr_sum += (ui_kb + ui_kr) / 2.0
                            
                            add_text(f"K_бак = ({K_T_b:.2f}+{K_W_b:.2f}+{center_KG_bak:.2f})/3 = {ui_kb:.3f}\n")
                            add_text(f"K_росл= ({K_T_r:.2f}+{K_W_r:.2f}+{K_P_r:.2f}+{center_KG_rosl:.2f})/4 = {ui_kr:.3f}\n")
                            add_text(f"K_прир = ({ui_kb:.2f}+{ui_kr:.2f})/2 = ")
                            add_text(f"{(ui_kb+ui_kr)/2:.3f}\n\n", "bold")
                        else:
                            total_K_pryr += K_bak_m
                            ui_k_pryr_sum += ui_kb
                            add_text(f"K_бак = ({K_T_b:.2f}+{K_W_b:.2f}+{center_KG_bak:.2f})/3 = {ui_kb:.3f}\n")
                            add_text(f"K_прир = K_бак = ")
                            add_text(f"{ui_kb:.3f}\n\n", "bold")

                        valid_months += 1
                except ValueError:
                    pass

            if valid_months > 0:
                avg_K_pryr = total_K_pryr / valid_months
                E_lab = biorem_coefficients_by_index.get(clean_idx, 0.5)
                eff_matrix = E_lab * avg_K_pryr
                
                ui_avg_kb = ui_k_bak_sum / valid_months
                
                add_text(L["txt_summary"], "bold_center")
                add_text(f"{L['txt_cycles']}{cycles_count:.1f}\n")
                add_text(f"{L['txt_avg_kb']}{ui_avg_kb:.3f}\n")
                
                if has_plants:
                    ui_avg_kr = ui_k_rosl_sum / valid_months
                    ui_avg_kp = ui_k_pryr_sum / valid_months
                    add_text(f"{L['txt_avg_kr']}{ui_avg_kr:.3f}\n")
                    add_text(f"{L['txt_avg_kp']}")
                    add_text(f"{ui_avg_kp:.3f}\n\n", "bold")
                else:
                    ui_avg_kp = ui_k_pryr_sum / valid_months
                    add_text(f"{L['txt_avg_kp']}")
                    add_text(f"{ui_avg_kp:.3f}\n\n", "bold")
                    
                final_val = E_lab * ui_avg_kp
                add_text(f"{L['txt_eff_lab']}{E_lab:.3f}\n")
                add_text(L["txt_final_formula"])
                add_text(f"({ui_avg_kp:.3f} × {E_lab:.3f}) = {final_val:.3f}\n", "bold")
                    
                if ui_avg_kp < 0.5:
                    warn_frame.pack(anchor="w", padx=10, fill="x", pady=(5,0))
                else:
                    warn_frame.pack_forget()

            else:
                eff_matrix = np.zeros_like(local_river_mask, dtype=np.float32)
                add_text(L["txt_no_data"])
                warn_frame.pack_forget()
        else:
            eff_matrix = np.zeros_like(local_river_mask, dtype=np.float32)
            add_text(L["txt_select_months"])
            warn_frame.pack_forget()

        degradation_multiplier = np.exp(-eff_matrix * time_factor)
        scalar_degradation = np.exp(-np.mean(eff_matrix) * time_factor)

        current_river_mass = sim_cache['base_total_river_mass'] * scalar_degradation
        current_river_mass = min(current_river_mass, vol_tons)
        if current_river_mass < 0.01: current_river_mass = 0.0
        river_mass_label.config(text=f"{current_river_mass:.2f}")

        base_spill = sim_cache['base_spill_intensity']
        base_spill_clipped = np.clip(base_spill, 0.0, max_c)
        
        if np.max(base_spill_clipped) > 1e-6:
            current_spill_intensity = base_spill_clipped * degradation_multiplier
        else:
            current_spill_intensity = np.zeros_like(base_spill)
            
        threshold = max(1.0, max_c * 0.02)
        current_spill_intensity[current_spill_intensity < threshold] = 0.0 

        base_river = sim_cache['base_river_intensity']
        base_river_clipped = np.clip(base_river, 0.0, max_c)
        
        if np.max(base_river_clipped) > 1e-5:
            current_river_intensity = base_river_clipped * degradation_multiplier
        else:
            current_river_intensity = np.zeros_like(base_river)
            
        current_river_intensity[current_river_intensity < (threshold * 0.1)] = 0.0
        current_river_intensity *= local_river_mask

        polluted_pixels = np.sum(current_spill_intensity > 0.0) 
        area_km2 = (polluted_pixels * pixel_area_m2) / 1000000.0
        area_label.config(text=f"{area_km2:.4f}")

        spill_array.fill(0)
        spill_array[r_min:r_max, c_min:c_max] = current_spill_intensity
        river_spill_array.fill(0)
        river_spill_array[r_min:r_max, c_min:c_max] = current_river_intensity
        
        spill_img.set_clim(vmin=0, vmax=max_c if max_c > 1e-3 else 1.0)

    else:
        spill_array.fill(0)
        river_spill_array.fill(0)
        river_mass_label.config(text="0.00")
        area_label.config(text="0.0000")
        spill_img.set_clim(vmin=0, vmax=float(max_conc.get()) if float(max_conc.get()) > 1e-3 else 1.0)

    calc_text.config(state=tk.DISABLED)
    spill_img.set_data(spill_array)
    spill_img.set_visible(var_height.get())

    for artist in river_spill_artists:
        try: artist.remove()
        except: pass
    river_spill_artists = []

    mask_idx = (spill_array > 0.0) | (river_spill_array > 0.0)
    
    if np.any(mask_idx) and not is_animating:
        shape_iter = shapes(mask_idx.astype(np.uint8), mask=mask_idx, transform=dem_transform)
        shapely_geoms = [shape(g) for g, v in shape_iter]
        if shapely_geoms:
            spill_zone = unary_union(shapely_geoms)
            buffer_dist = abs(dem_transform.a) * 4.0
            spill_zone = spill_zone.buffer(buffer_dist).buffer(-buffer_dist * 0.8)
            
            possible_matches_index = rivers_plot.sindex.query(spill_zone, predicate="intersects")
            if len(possible_matches_index) > 0:
                river_candidates = rivers_plot.iloc[possible_matches_index]
                clipped_rivers = river_candidates.geometry.intersection(spill_zone)
                clipped_rivers = clipped_rivers[~clipped_rivers.is_empty]
                if not clipped_rivers.empty:
                    old_cols = len(ax.collections)
                    old_lines = len(ax.lines)
                    cur_xlim_tmp, cur_ylim_tmp = ax.get_xlim(), ax.get_ylim()
                    
                    clipped_rivers.plot(ax=ax, color="#ff0000", linewidth=4.0, zorder=10.6)
                    
                    ax.set_xlim(cur_xlim_tmp)
                    ax.set_ylim(cur_ylim_tmp)
                    ax.set_aspect(geo_aspect, adjustable='datalim')
                    river_spill_artists = ax.collections[old_cols:] + ax.lines[old_lines:]
                    for artist in river_spill_artists:
                        artist.set_visible(var_rivers.get())
    
    canvas.draw_idle()

def start_remediation_process():
    global timeline_value, is_animating
    if spill_lon is None or spill_lat is None or is_spreading:
        return  
    
    is_animating = True
    timeline_value = 0.0  
    run_animation_step()

def run_animation_step():
    global timeline_value, is_animating
    if not is_animating: 
        return
        
    timeline_value += 0.01  
    if timeline_value >= 1.0:
        timeline_value = 1.0
        draw_timeline()
        is_animating = False 
        apply_remediation_and_draw()       
        return
        
    draw_timeline()   
    apply_remediation_and_draw()    
    
    root.after(20, run_animation_step)

def pause_anim():
    global is_animating
    is_animating = False

def play_anim():
    global is_animating, timeline_value
    if spill_lon is None or spill_lat is None or is_spreading:
        return
    if not is_animating and timeline_value < 1.0:
        is_animating = True
        run_animation_step()

def restart_anim():
    global timeline_value, is_animating
    if spill_lon is None or spill_lat is None or is_spreading:
        return
    is_animating = False
    timeline_value = 0.0
    draw_timeline()
    apply_remediation_and_draw()

def zoom_factory(event):
    if event.xdata is None or event.ydata is None: return
    base_scale = 1.20
    scale_factor = 1 / base_scale if event.button == 'up' else base_scale
    cur_xlim, cur_ylim = ax.get_xlim(), ax.get_ylim()
    
    new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
    new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor
    
    rel_x = (event.xdata - cur_xlim[0]) / (cur_xlim[1] - cur_xlim[0])
    rel_y = (event.ydata - cur_ylim[0]) / (cur_ylim[1] - cur_ylim[0])
    
    ax.set_xlim([event.xdata - new_width * rel_x, event.xdata + new_width * (1 - rel_x)])
    ax.set_ylim([event.ydata - new_height * rel_y, event.ydata + new_height * (1 - rel_y)])
    canvas.draw_idle()

def on_press(event):
    global is_panning, pan_last_x, pan_last_y
    if event.button in [1, 3]:
        if event.dblclick:
            on_click(event)
        else:
            is_panning = True
            pan_last_x, pan_last_y = event.x, event.y

def on_release(event): 
    global is_panning
    is_panning = False

def on_motion(event):
    global pan_last_x, pan_last_y
    L = LANG_DATA[current_lang]
    if is_panning and event.x is not None and event.y is not None:
        bbox = ax.get_window_extent()
        xlim, ylim = ax.get_xlim(), ax.get_ylim()
        dx = (event.x - pan_last_x) * (xlim[1] - xlim[0]) / bbox.width
        dy = (event.y - pan_last_y) * (ylim[1] - ylim[0]) / bbox.height
        ax.set_xlim(xlim[0] - dx, xlim[1] - dx)
        ax.set_ylim(ylim[0] - dy, ylim[1] - dy)
        pan_last_x, pan_last_y = event.x, event.y
        canvas.draw_idle()
        return

    if event.xdata is not None and event.ydata is not None:
        h_txt, s_txt = get_height_and_soil(event.xdata, event.ydata)
        height_label.config(text=h_txt)
        soil_label.config(text=s_txt)
        
        c, r = dem_inv_transform * (event.xdata, event.ydata)
        r, c = int(round(r)), int(round(c))
        current_conc = spill_array[r, c] if (0 <= r < spill_array.shape[0] and 0 <= c < spill_array.shape[1]) else 0.0
        
        try:
            m_c = float(max_conc.get())
        except ValueError:
            m_c = 1.0
            
        current_conc = min(current_conc, m_c)
        
        if current_conc > 0:
            intensity_label.config(text=f"{current_conc:.2f} {L['unit_mg_kg']}")
        else:
            intensity_label.config(text=f"0.00 {L['unit_mg_kg']}")

def on_click(event):
    global spill_lon, spill_lat
    if event.xdata is None or event.ydata is None: return
    spill_lon, spill_lat = event.xdata, event.ydata
    coord_lon_var.set(f"{spill_lon:.4f}")
    coord_lat_var.set(f"{spill_lat:.4f}")
    
    spill_marker.set_data([spill_lon], [spill_lat])
    canvas.draw_idle()

    def apply_default_climate():
        default_t = [-3, -2, 3, 10, 16, 20, 22, 21, 15, 8, 3, -1]
        default_h = [85, 80, 75, 65, 60, 65, 65, 60, 70, 75, 85, 85]
        default_p = [40, 35, 40, 45, 55, 70, 70, 60, 50, 40, 45, 45]
        for i in range(12):
            climate_entries[i]['T'].delete(0, tk.END)
            climate_entries[i]['H'].delete(0, tk.END)
            climate_entries[i]['P'].delete(0, tk.END)
            
            climate_entries[i]['T'].insert(0, str(default_t[i]))
            climate_entries[i]['H'].insert(0, str(default_h[i]))
            climate_entries[i]['P'].insert(0, str(default_p[i]))
        save_climate_year()

    if monthly_t2m is not None and monthly_d2m is not None and monthly_tp is not None:
        try:
            local_t2m = monthly_t2m.sel(longitude=spill_lon, latitude=spill_lat, method='nearest').values
            local_d2m = monthly_d2m.sel(longitude=spill_lon, latitude=spill_lat, method='nearest').values
            local_tp = monthly_tp.sel(longitude=spill_lon, latitude=spill_lat, method='nearest').values
            
            if np.nanmean(local_t2m) > 200: local_t2m = local_t2m - 273.15
            if np.nanmean(local_d2m) > 200: local_d2m = local_d2m - 273.15
                
            RH = 100 * np.exp((17.625 * local_d2m) / (243.04 + local_d2m) - (17.625 * local_t2m) / (243.04 + local_t2m))
            RH = np.clip(RH, 0, 100)
            
            local_tp_mm = local_tp * 1000 
            if np.nanmean(local_tp_mm) < 15: 
                days_in_month = np.array([31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
                local_tp_mm = local_tp_mm * days_in_month
                
            for i in range(12):
                climate_entries[i]['T'].delete(0, tk.END)
                climate_entries[i]['H'].delete(0, tk.END)
                climate_entries[i]['P'].delete(0, tk.END)
                
                climate_entries[i]['T'].insert(0, str(int(round(local_t2m[i]))))
                climate_entries[i]['H'].insert(0, str(int(round(RH[i]))))
                climate_entries[i]['P'].insert(0, str(int(round(local_tp_mm[i]))))
            
            save_climate_year() 
        except Exception as e:
            apply_default_climate()
    else:
        apply_default_climate()
            
    request_update()

def redraw():
    dem_img.set_visible(var_height.get())
    spill_img.set_visible(var_height.get())
    soil_img.set_visible(var_soil.get())
    for artist in river_artists: artist.set_visible(var_rivers.get())
    for artist in river_spill_artists: artist.set_visible(var_rivers.get())
    canvas.draw_idle()

def update_timeline_handle(event):
    global timeline_value
    w = timeline_canvas.winfo_width()
    if w < 100: w = 800
    padding = 60
    x_start, x_end = padding, w - padding
    
    cx = event.x
    if cx < x_start: cx = x_start
    if cx > x_end: cx = x_end
    
    timeline_value = (cx - x_start) / (x_end - x_start) if x_end != x_start else 0.0
    draw_timeline()
    schedule_update()

def get_all_timeline_items():
    if not month_vars: return []
    temp_dict = {k: v.copy() for k, v in climate_data_by_year.items()}
    current_year_data = temp_dict.get(current_year, {}).copy()
    for i in range(12):
        if i not in current_year_data: current_year_data[i] = {}
        try: current_year_data[i]['checked'] = month_vars[i][1].get()
        except IndexError: pass
    temp_dict[current_year] = current_year_data
    
    items = []
    months_names = LANG_DATA[current_lang]["months"]
    for y in sorted(temp_dict.keys()):
        sel = [i for i in range(12) if temp_dict[y].get(i, {}).get('checked', False)]
        if sel:
            items.append(('year', str(y)))
            for i in sel: items.append(('month', months_names[i]))
    return items

def draw_timeline(event=None):
    if 'timeline_canvas' not in globals(): return
    
    if 'month_vars' in globals() and 'odd_months_warn_lbl' in globals():
        active_count = sum(1 for m, var in month_vars if var.get())
        if active_count > 0 and active_count % 2 != 0:
            odd_months_warn_lbl.pack(anchor="w")
        else:
            odd_months_warn_lbl.pack_forget()

    w = timeline_canvas.winfo_width()
    if w < 100: w = 800
    h = 50
    padding = 60
    x_start, x_end = padding, w - padding
    y = h // 2 - 5

    timeline_canvas.delete("all")
    timeline_canvas.create_line(x_start, y, x_end, y, fill="red", width=3)

    r_bound = 6
    timeline_canvas.create_oval(x_start - r_bound, y - r_bound, x_start + r_bound, y + r_bound, fill="red", outline="red")
    timeline_canvas.create_oval(x_end - r_bound, y - r_bound, x_end + r_bound, y + r_bound, fill="red", outline="red")

    items = get_all_timeline_items()
    num_marks = len(items)

    mark_positions = []
    if num_marks == 1:
        mark_positions.append(((x_start + x_end) / 2, items[0][0], items[0][1]))
    elif num_marks > 1:
        for idx in range(num_marks):
            pos_x = x_start + (x_end - x_start) * idx / (num_marks - 1)
            mark_positions.append((pos_x, items[idx][0], items[idx][1]))

    for pos_x, itype, text in mark_positions:
        if itype == 'year':
            timeline_canvas.create_text(pos_x, y - 16, text=text, font=("Arial", 10, "bold"), fill="#b30000")
            timeline_canvas.create_line(pos_x, y - 5, pos_x, y + 5, fill="red", width=2)
        else:
            timeline_canvas.create_oval(pos_x - 4, y - 4, pos_x + 4, y + 4, fill="white", outline="red", width=2)
            timeline_canvas.create_text(pos_x, y + 18, text=text, font=("Arial", 9, "bold"), fill="black")

    hx = x_start + (x_end - x_start) * timeline_value
    r_handle = 7
    timeline_canvas.create_oval(hx - r_handle, y - r_handle, hx + r_handle, y + r_handle, fill="black", outline="black")

def zoom_to_spill():
    mask_idx = (spill_array > 0.0) | (river_spill_array > 0.0)
    if np.any(mask_idx):
        rows, cols = np.where(mask_idx)
        r_min_idx, r_max_idx = np.min(rows), np.max(rows)
        c_min_idx, c_max_idx = np.min(cols), np.max(cols)

        p1 = dem_transform * (c_min_idx, r_min_idx)
        p2 = dem_transform * (c_max_idx + 1, r_max_idx + 1)

        x_min_spill = min(p1[0], p2[0])
        x_max_spill = max(p1[0], p2[0])
        y_min_spill = min(p1[1], p2[1])
        y_max_spill = max(p1[1], p2[1])

        dx = x_max_spill - x_min_spill
        dy = y_max_spill - y_min_spill

        margin_x = max(dx * 0.15, 0.005 if is_geo else 500.0)
        margin_y = max(dy * 0.15, 0.005 if is_geo else 500.0)

        ax.set_xlim(x_min_spill - margin_x, x_max_spill + margin_x)
        ax.set_ylim(y_min_spill - margin_y, y_max_spill + margin_y)
        canvas.draw_idle()
    elif spill_lon is not None and spill_lat is not None:
        delta = 0.05 if is_geo else 5000.0
        ax.set_xlim(spill_lon - delta, spill_lon + delta)
        ax.set_ylim(spill_lat - delta, spill_lat + delta)
        canvas.draw_idle()

# --- Функція зміни мови ---
def change_language(selected_lang):
    global current_lang
    old_lang = current_lang
    current_lang = "UA" if selected_lang == "Українська" else "EN"
    if old_lang == current_lang:
        return
    
    L = LANG_DATA[current_lang]
    
    # Переклад вибору очищення
    old_options = LANG_DATA[old_lang]["clean_options"]
    new_options = L["clean_options"]
    current_val = clean_var.get()
    if current_val in old_options:
        idx = old_options.index(current_val)
        clean_var.set(new_options[idx])
    else:
        clean_var.set(new_options[0])
        
    menu = clean_menu["menu"]
    menu.delete(0, "end")
    for opt in new_options:
        menu.add_command(label=opt, command=lambda v=opt: [clean_var.set(v), schedule_update()])
        
    # Оновлення написів у вікні
    root.title(L["title"])
    right_header_lbl.config(text=L["right_header"])
    lbl_lang.config(text=L["lbl_lang"])
    
    sec_layers_lbl.config(text=L["sec_layers"])
    chk_height_cb.config(text=L["chk_height"])
    chk_soil_cb.config(text=L["chk_soil"])
    chk_rivers_cb.config(text=L["chk_rivers"])
    
    sec_local_lbl.config(text=L["sec_local"])
    lbl_coords.config(text=L["lbl_coords"])
    lbl_lat.config(text=L["lbl_lat"])
    lbl_lon.config(text=L["lbl_lon"])
    lbl_max_conc.config(text=L["lbl_max_conc"])
    unit_mg_kg1.config(text=L["unit_mg_kg"])
    lbl_volume.config(text=L["lbl_volume"])
    unit_tons1.config(text=L["unit_tons"])
    lbl_river_mass.config(text=L["lbl_river_mass"])
    unit_tons2.config(text=L["unit_tons"])
    lbl_area.config(text=L["lbl_area"])
    unit_km2.config(text=L["unit_km2"])
    lbl_intensity.config(text=L["lbl_intensity"])
    
    sec_cleaning_lbl.config(text=L["sec_cleaning"])
    lbl_clean_type.config(text=L["lbl_clean_type"])
    
    sec_climate_lbl.config(text=L["sec_climate"])
    odd_months_warn_lbl.config(text=L["odd_warn"])
    tb_month_lbl.config(text=L["tb_month"])
    tb_temp_lbl.config(text=L["tb_temp"])
    tb_hum_lbl.config(text=L["tb_hum"])
    tb_precip_lbl.config(text=L["tb_precip"])
    
    for i in range(12):
        month_checkbuttons[i].config(text=L["months"][i])
        
    warn_lbl.config(text=L["bio_warn"])
    btn_update.config(text=L["btn_update"])
    btn_clear.config(text=L["btn_clear"])
    lbl_timeline.config(text=L["lbl_timeline"])
    
    draw_timeline()
    update_scalebar()
    request_update()

root = tk.Tk()
root.title(LANG_DATA["UA"]["title"])
root.geometry("1400x850")
root_bg = root.cget("bg")

PADY = 5
left = tk.Frame(root, width=320, bg="#d8d2b0")
left.pack(side=tk.LEFT, fill=tk.Y)
left.pack_propagate(False)

right_panel = tk.Frame(root, width=320, bg="#d8d2b0")
right_panel.pack(side=tk.RIGHT, fill=tk.Y)
right_panel.pack_propagate(False)

right_header_lbl = tk.Label(right_panel, text=LANG_DATA["UA"]["right_header"], bg="#d8d2b0", font=("Arial", 11, "bold"))
right_header_lbl.pack(anchor="n", pady=(10, 5))

calc_text = tk.Text(right_panel, bg="white", font=("Courier", 9), wrap=tk.WORD, state=tk.DISABLED)
calc_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 15))

center_container = tk.Frame(root)
center_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# --- ПЕРЕМИКАЧ МОВИ ---
lang_frame = tk.Frame(left, bg="#d8d2b0")
lang_frame.pack(anchor="w", padx=10, fill="x", pady=(10, 5))

lbl_lang = tk.Label(lang_frame, text=LANG_DATA["UA"]["lbl_lang"], bg="#d8d2b0", font=("Arial", 9, "bold"))
lbl_lang.pack(side="left")

lang_var = tk.StringVar(value="Українська")
lang_menu = tk.OptionMenu(lang_frame, lang_var, "Українська", "English", command=change_language)
lang_menu.config(width=10, bg="white", activebackground="white", highlightthickness=0)
lang_menu["menu"].config(bg="white")
lang_menu.pack(side="right")

# --- ШАРИ ---
sec_layers_lbl = tk.Label(left, text=LANG_DATA["UA"]["sec_layers"], bg="#d8d2b0", font=("Arial", 11, "bold"))
sec_layers_lbl.pack(anchor="w", padx=10, pady=(5, 5))

row1 = tk.Frame(left, bg="#d8d2b0")
row1.pack(fill="x", padx=10, pady=(0, 5))
var_height = tk.BooleanVar(value=True)
chk_height_cb = tk.Checkbutton(row1, text=LANG_DATA["UA"]["chk_height"], variable=var_height, command=redraw, bg="#d8d2b0")
chk_height_cb.pack(side="left")
height_label = tk.Label(row1, text="— м", bg="#d8d2b0")
height_label.pack(side="right")

row2 = tk.Frame(left, bg="#d8d2b0")
row2.pack(fill="x", padx=10, pady=(0, 5))
var_soil = tk.BooleanVar(value=False)
chk_soil_cb = tk.Checkbutton(row2, text=LANG_DATA["UA"]["chk_soil"], variable=var_soil, command=redraw, bg="#d8d2b0")
chk_soil_cb.pack(side="left")
soil_label = tk.Label(row2, text="—", bg="#d8d2b0")
soil_label.pack(side="right")

row3 = tk.Frame(left, bg="#d8d2b0")
row3.pack(fill="x", padx=10, pady=(0, 5))
var_rivers = tk.BooleanVar(value=False)
chk_rivers_cb = tk.Checkbutton(row3, text=LANG_DATA["UA"]["chk_rivers"], variable=var_rivers, command=redraw, bg="#d8d2b0")
chk_rivers_cb.pack(side="left")

# --- ЛОКАЛЬНИЙ СТАН ---
sec_local_lbl = tk.Label(left, text=LANG_DATA["UA"]["sec_local"], bg="#d8d2b0", font=("Arial", 11, "bold"))
sec_local_lbl.pack(anchor="w", padx=10, pady=(10, 5))

coord_row = tk.Frame(left, bg="#d8d2b0")
coord_row.pack(anchor="w", padx=10, fill="x", pady=PADY)
lbl_coords = tk.Label(coord_row, text=LANG_DATA["UA"]["lbl_coords"], bg="#d8d2b0")
lbl_coords.pack(side="left")
coords_values = tk.Frame(coord_row, bg="#d8d2b0")
coords_values.pack(side="right")

lat_row = tk.Frame(coords_values, bg="#d8d2b0")
lat_row.pack(anchor="e", pady=2)
lbl_lat = tk.Label(lat_row, text=LANG_DATA["UA"]["lbl_lat"], bg="#d8d2b0")
lbl_lat.pack(side="left")
coord_lat_var = tk.StringVar()
ent_lat = tk.Entry(lat_row, width=12, textvariable=coord_lat_var, justify="center")
ent_lat.pack(side="left")

ton_row = tk.Frame(coords_values, bg="#d8d2b0")
ton_row.pack(anchor="e", pady=2)
lbl_lon = tk.Label(ton_row, text=LANG_DATA["UA"]["lbl_lon"], bg="#d8d2b0")
lbl_lon.pack(side="left")
coord_lon_var = tk.StringVar()
ent_lon = tk.Entry(ton_row, width=12, textvariable=coord_lon_var, justify="center")
ent_lon.pack(side="left")

conc_row = tk.Frame(left, bg="#d8d2b0")
conc_row.pack(anchor="w", padx=10, fill="x", pady=PADY)
lbl_max_conc = tk.Label(conc_row, text=LANG_DATA["UA"]["lbl_max_conc"], bg="#d8d2b0")
lbl_max_conc.pack(side="left")
max_conc = tk.DoubleVar(value=622.4)
sb_conc = tk.Spinbox(conc_row, from_=0.01, to=1000000.0, increment=1.0, width=12, textvariable=max_conc)
sb_conc.pack(side="left")
unit_mg_kg1 = tk.Label(conc_row, text=LANG_DATA["UA"]["unit_mg_kg"], bg="#d8d2b0")
unit_mg_kg1.pack(side="left")

volume_row = tk.Frame(left, bg="#d8d2b0")
volume_row.pack(anchor="w", padx=10, fill="x", pady=PADY)
lbl_volume = tk.Label(volume_row, text=LANG_DATA["UA"]["lbl_volume"], bg="#d8d2b0")
lbl_volume.pack(side="left")
volume_var = tk.DoubleVar(value=1000.0)
sb_vol = tk.Spinbox(volume_row, from_=0.05, to=10000.0, increment=0.01, width=10, textvariable=volume_var)
sb_vol.pack(side="left")
unit_tons1 = tk.Label(volume_row, text=LANG_DATA["UA"]["unit_tons"], bg="#d8d2b0")
unit_tons1.pack(side="left")

river_mass_row = tk.Frame(left, bg="#d8d2b0")
river_mass_row.pack(anchor="w", padx=10, fill="x", pady=PADY)
lbl_river_mass = tk.Label(river_mass_row, text=LANG_DATA["UA"]["lbl_river_mass"], bg="#d8d2b0")
lbl_river_mass.pack(side="left")
river_mass_label = tk.Label(river_mass_row, text="0.00", bg="white", width=12, anchor="w", padx=5, bd=1, relief="sunken")
river_mass_label.pack(side="left", padx=5)
unit_tons2 = tk.Label(river_mass_row, text=LANG_DATA["UA"]["unit_tons"], bg="#d8d2b0")
unit_tons2.pack(side="left")

area_row = tk.Frame(left, bg="#d8d2b0")
area_row.pack(anchor="w", padx=10, fill="x", pady=PADY)
lbl_area = tk.Label(area_row, text=LANG_DATA["UA"]["lbl_area"], bg="#d8d2b0")
lbl_area.pack(side="left")
area_label = tk.Label(area_row, text="0.0000", bg="white", width=12, anchor="w", padx=5, bd=1, relief="sunken")
area_label.pack(side="left", padx=5)
unit_km2 = tk.Label(area_row, text=LANG_DATA["UA"]["unit_km2"], bg="#d8d2b0")
unit_km2.pack(side="left")

intensity_row = tk.Frame(left, bg="#d8d2b0")
intensity_row.pack(anchor="w", padx=10, fill="x", pady=PADY)
lbl_intensity = tk.Label(intensity_row, text=LANG_DATA["UA"]["lbl_intensity"], bg="#d8d2b0")
lbl_intensity.pack(side="left")
intensity_label = tk.Label(intensity_row, text=f"0.00 {LANG_DATA['UA']['unit_mg_kg']}", bg="white", width=22, anchor="w", padx=5)
intensity_label.pack(side="left")

# --- ОЧИЩЕННЯ ГРУНТУ ---
sec_cleaning_lbl = tk.Label(left, text=LANG_DATA["UA"]["sec_cleaning"], bg="#d8d2b0", font=("Arial", 11, "bold"))
sec_cleaning_lbl.pack(anchor="w", padx=10, pady=(10, 5))

clean_row = tk.Frame(left, bg="#d8d2b0")
clean_row.pack(anchor="w", padx=10, fill="x", pady=PADY)
lbl_clean_type = tk.Label(clean_row, text=LANG_DATA["UA"]["lbl_clean_type"], bg="#d8d2b0")
lbl_clean_type.pack(side="left")
clean_var = tk.StringVar(value=LANG_DATA["UA"]["clean_options"][0])
clean_menu = tk.OptionMenu(clean_row, clean_var, *LANG_DATA["UA"]["clean_options"], command=lambda v: schedule_update())
clean_menu.config(width=20, bg="white", activebackground="white", highlightthickness=0)
clean_menu["menu"].config(bg="white")
clean_menu.pack(side="left", padx=5)

# --- КЛІМАТИЧНІ УМОВИ ---
sec_climate_lbl = tk.Label(left, text=LANG_DATA["UA"]["sec_climate"], bg="#d8d2b0", font=("Arial", 11, "bold"))
sec_climate_lbl.pack(anchor="w", padx=10, pady=(10, 5))

climate_frame = tk.Frame(left, bg="#d8d2b0", bd=1, relief="solid")
climate_frame.pack(anchor="w", padx=10, fill="x", pady=0)

odd_warn_frame = tk.Frame(left, bg="#d8d2b0")
odd_warn_frame.pack(anchor="w", padx=10, fill="x", pady=(2,0))
odd_months_warn_lbl = tk.Label(odd_warn_frame, text=LANG_DATA["UA"]["odd_warn"], fg="red", bg="#d8d2b0", font=("Arial", 10, "bold"))
odd_months_warn_lbl.pack_forget()

h_bg = "#e8e2c0"
font_small = ("Arial", 8)

current_year = 2026
climate_data_by_year = {}
climate_entries = []

def save_climate_year():
    global current_year
    year_data = {}
    for i in range(12):
        year_data[i] = {
            'checked': month_vars[i][1].get(),
            'T': climate_entries[i]['T'].get(),
            'H': climate_entries[i]['H'].get(),
            'P': climate_entries[i]['P'].get()
        }
    climate_data_by_year[current_year] = year_data

def load_climate_year():
    global current_year
    year_data = climate_data_by_year.get(current_year, {})
    for i in range(12):
        month_vars[i][1].set(year_data.get(i, {}).get('checked', False))
        for key in ['T', 'H', 'P']:
            climate_entries[i][key].delete(0, tk.END)
            val = year_data.get(i, {}).get(key, '')
            climate_entries[i][key].insert(0, val)
    draw_timeline()

def change_year(delta):
    global current_year
    save_climate_year()
    current_year += delta
    year_label.config(text=str(current_year))
    load_climate_year()

year_nav_bg = "#d0c9a0"
year_nav_frame = tk.Frame(climate_frame, bg=year_nav_bg)
year_nav_frame.grid(row=0, column=0, columnspan=4, sticky="nsew")

tk.Button(year_nav_frame, text="◀", command=lambda: change_year(-1), relief="flat", bg=year_nav_bg, width=2, font=("Arial", 9, "bold")).pack(side="left", padx=2)
year_label = tk.Label(year_nav_frame, text=str(current_year), bg=year_nav_bg, font=("Arial", 10, "bold"))
year_label.pack(side="left", expand=True)
tk.Button(year_nav_frame, text="▶", command=lambda: change_year(1), relief="flat", bg=year_nav_bg, width=2, font=("Arial", 9, "bold")).pack(side="right", padx=2)

tb_month_lbl = tk.Label(climate_frame, text=LANG_DATA["UA"]["tb_month"], bg=h_bg, bd=1, relief="solid", font=font_small)
tb_month_lbl.grid(row=1, column=0, sticky="nsew")
tb_temp_lbl = tk.Label(climate_frame, text=LANG_DATA["UA"]["tb_temp"], bg=h_bg, bd=1, relief="solid", font=font_small)
tb_temp_lbl.grid(row=1, column=1, sticky="nsew")
tb_hum_lbl = tk.Label(climate_frame, text=LANG_DATA["UA"]["tb_hum"], bg=h_bg, bd=1, relief="solid", font=font_small)
tb_hum_lbl.grid(row=1, column=2, sticky="nsew")
tb_precip_lbl = tk.Label(climate_frame, text=LANG_DATA["UA"]["tb_precip"], bg=h_bg, bd=1, relief="solid", font=font_small)
tb_precip_lbl.grid(row=1, column=3, sticky="nsew")

month_checkbuttons = []
for i, month in enumerate(LANG_DATA["UA"]["months"]):
    row_idx = i + 2
    m_var = tk.BooleanVar(value=False)
    month_vars.append((month, m_var))
    
    cb = tk.Checkbutton(climate_frame, text=month, variable=m_var, command=lambda: draw_timeline(), bg="#d8d2b0", bd=1, relief="solid", font=font_small, anchor="w", highlightthickness=0, pady=0)
    cb.grid(row=row_idx, column=0, sticky="nsew")
    month_checkbuttons.append(cb)
    
    ent_t = tk.Entry(climate_frame, width=5, font=font_small)
    ent_t.grid(row=row_idx, column=1, sticky="nsew", padx=1, pady=1)
    ent_t.bind("<KeyRelease>", lambda e: save_climate_year())
    
    ent_h = tk.Entry(climate_frame, width=5, font=font_small)
    ent_h.grid(row=row_idx, column=2, sticky="nsew", padx=1, pady=1)
    ent_h.bind("<KeyRelease>", lambda e: save_climate_year())
    
    ent_p = tk.Entry(climate_frame, width=5, font=font_small)
    ent_p.grid(row=row_idx, column=3, sticky="nsew", padx=1, pady=1)
    ent_p.bind("<KeyRelease>", lambda e: save_climate_year())
    
    climate_entries.append({'T': ent_t, 'H': ent_h, 'P': ent_p})

for col in range(4):
    climate_frame.grid_columnconfigure(col, weight=1)

warn_frame = tk.Frame(left, bg="#d8d2b0")
warn_lbl = tk.Label(warn_frame, text=LANG_DATA["UA"]["bio_warn"], fg="black", bg="#d8d2b0", font=("Arial", 9, "bold"), justify="left")
warn_lbl.pack(anchor="w")
warn_line = tk.Frame(warn_frame, bg="red", height=2)
warn_line.pack(fill="x", pady=(0, 5))
warn_frame.pack_forget()

bottom_buttons_frame = tk.Frame(left, bg="#d8d2b0")
bottom_buttons_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=15, pady=(0, 15))
btn_update = tk.Button(bottom_buttons_frame, text=LANG_DATA["UA"]["btn_update"], command=btn_update_data_click, bg="#ffcccb", font=("Arial", 10, "bold"))
btn_update.pack(fill=tk.X, pady=(0, 8))
btn_clear = tk.Button(bottom_buttons_frame, text=LANG_DATA["UA"]["btn_clear"], command=clear_data, bg="#cccccc", font=("Arial", 10, "bold"), fg="black")
btn_clear.pack(fill=tk.X)

fig, ax = plt.subplots(figsize=(8, 8), gridspec_kw={'left': 0, 'right': 1, 'bottom': 0, 'top': 1})
fig.subplots_adjust(left=0, right=1, bottom=0, top=1, wspace=0, hspace=0)
ax.margins(0, 0)
ax.axis("off")
ax.set_aspect(geo_aspect, adjustable='datalim')

valid_dem = dem[~np.isnan(dem)]
vmin, vmax = np.nanmin(dem), np.nanmax(dem) if len(valid_dem) > 0 else (0, 1)
norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)
cmap = plt.get_cmap("terrain")
dem_rgba = cmap(norm(dem))
dem_rgba[np.isnan(dem), 3] = 0.0

dem_img = ax.imshow(dem_rgba, extent=extent, interpolation='none', resample=False, rasterized=True)

soil_norm = mpl.colors.Normalize(vmin=np.nanmin(soil), vmax=np.nanmax(soil))
soil_cmap = plt.get_cmap("YlGn")
soil_rgba = soil_cmap(soil_norm(soil))
soil_rgba[..., 3] = np.where(soil == 0, 0.0, 0.35) 
soil_img = ax.imshow(soil_rgba, extent=extent, interpolation='none', resample=False)
soil_img.set_visible(False)

# Градієнт колірної палітри плями:
# 0% - прозорий зелений, >0% - зелений, далі через жовто-зелений, жовтий, помаранчевий до 100% - червоний
colors_palette = [
    (0.0,   (0.0, 1.0, 0.0, 0.0)),   # 0% - повністю прозорий
    (0.001, (0.0, 1.0, 0.0, 0.8)),   # >0% - зелений
    (0.25,  (0.5, 1.0, 0.0, 0.8)),   # 25% - жовто-зелений
    (0.50,  (1.0, 1.0, 0.0, 0.8)),   # 50% - жовтий
    (0.75,  (1.0, 0.5, 0.0, 0.8)),   # 75% - помаранчевий
    (1.00,  (1.0, 0.0, 0.0, 0.8))    # 100% - червоний
]
spill_cmap = LinearSegmentedColormap.from_list("spill_cmap", colors_palette, N=512)

spill_img = ax.imshow(spill_array, cmap=spill_cmap, extent=extent, interpolation='bilinear', vmin=0, vmax=1.0, zorder=10)
spill_marker, = ax.plot([], [], 'x', color='black', markersize=10, markeredgewidth=2, zorder=11)
border_plot.boundary.plot(ax=ax, color="black", linewidth=1.0)

num_cols = len(ax.collections)
num_lines = len(ax.lines)

rivers_plot.plot(ax=ax, color="blue", linewidth=4.0)
river_artists = ax.collections[num_cols:] + ax.lines[num_lines:]
for artist in river_artists: artist.set_visible(False)

ax.autoscale(False)

scale_line = ax.plot([], [], color='black', lw=2, transform=ax.transAxes, zorder=100, clip_on=False)[0]
num_segments = 4
scale_ticks = [ax.plot([], [], color='black', lw=2, transform=ax.transAxes, zorder=100, clip_on=False)[0] for _ in range(num_segments + 1)]
scale_texts = [ax.text(0, 0, '', transform=ax.transAxes, fontsize=10, ha='center', va='bottom', 
                       color='black', weight='bold', bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1), zorder=100, clip_on=False) 
               for _ in range(num_segments + 1)]

def update_scalebar(*args):
    L = LANG_DATA[current_lang]
    x_min, x_max = ax.get_xlim()
    y_min, y_max = ax.get_ylim()
    data_width = x_max - x_min
    if data_width <= 0: return

    if 'is_geo' in globals() and is_geo:
        center_lat = (y_min + y_max) / 2
        m_per_unit = 111320.0 * np.cos(np.radians(center_lat))
    else:
        m_per_unit = 1.0

    target_width_m = data_width * m_per_unit * 0.75
    if target_width_m <= 0: return

    magnitude = 10 ** np.floor(np.log10(target_width_m))
    val = target_width_m / magnitude
    if val < 2: nice_val = 1
    elif val < 5: nice_val = 2
    else: nice_val = 5
    scale_m = nice_val * magnitude

    scale_data_units = scale_m / m_per_unit
    frac_width = scale_data_units / data_width

    base_x = 0.05
    base_y = -0.05  # Лінійка опущена нижче і не торкається мапи
    tick_h = 0.015

    scale_line.set_data([base_x, base_x + frac_width], [base_y, base_y])

    segment_frac = frac_width / num_segments
    segment_m = scale_m / num_segments
    is_km = scale_m >= 1000

    for i in range(num_segments + 1):
        tx = base_x + i * segment_frac
        scale_ticks[i].set_data([tx, tx], [base_y - tick_h/2, base_y + tick_h/2])

        val_m = i * segment_m
        if is_km:
            val_display = val_m / 1000
            unit_str = L["unit_km"] if i == num_segments else ""
        else:
            val_display = val_m
            unit_str = L["unit_m"] if i == num_segments else ""

        scale_texts[i].set_text(f"{val_display:g}{unit_str}")
        scale_texts[i].set_position((tx, base_y + 0.015))

ax.callbacks.connect('xlim_changed', update_scalebar)
ax.callbacks.connect('ylim_changed', update_scalebar)

canvas = FigureCanvasTkAgg(fig, center_container)
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

# --- Реалістична векторна кнопка-лупа ---
zoom_btn_canvas = tk.Canvas(
    canvas.get_tk_widget(),
    width=44,
    height=44,
    bg="white",
    highlightthickness=1,
    highlightbackground="#cbd5e1",
    cursor="hand2"
)
zoom_btn_canvas.place(relx=1.0, rely=1.0, anchor="se", x=-15, y=-15)

def draw_magnifier_icon(hover=False, pressed=False):
    zoom_btn_canvas.delete("all")
    bg_color = "#e2e8f0" if pressed else ("#f1f5f9" if hover else "#ffffff")
    zoom_btn_canvas.configure(bg=bg_color)
    
    # Тінь кнопки / фон
    zoom_btn_canvas.create_oval(2, 2, 42, 42, fill=bg_color, outline="#94a3b8", width=1)
    
    # Лінза та метал
    zoom_btn_canvas.create_oval(11, 11, 27, 27, outline="#334155", width=2, fill="#e0f2fe")
    zoom_btn_canvas.create_line(24, 24, 33, 33, fill="#334155", width=3, capstyle="round")

draw_magnifier_icon()

zoom_btn_canvas.bind("<Enter>", lambda e: draw_magnifier_icon(hover=True))
zoom_btn_canvas.bind("<Leave>", lambda e: draw_magnifier_icon(hover=False))
zoom_btn_canvas.bind("<Button-1>", lambda e: [draw_magnifier_icon(hover=True, pressed=True), zoom_to_spill()])
zoom_btn_canvas.bind("<ButtonRelease-1>", lambda e: draw_magnifier_icon(hover=True, pressed=False))

# Прив'язка подій миші до полотна Matplotlib
canvas.mpl_connect('scroll_event', zoom_factory)
canvas.mpl_connect('button_press_event', on_press)
canvas.mpl_connect('button_release_event', on_release)
canvas.mpl_connect('motion_notify_event', on_motion)

# Прив'язка таймлайну
timeline_canvas = tk.Canvas(center_container, height=50, bg="#f0f0f0", highlightthickness=0)
timeline_canvas.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)

timeline_canvas.bind("<Button-1>", update_timeline_handle)
timeline_canvas.bind("<B1-Motion>", update_timeline_handle)
timeline_canvas.bind("<Configure>", draw_timeline)

# Панель керування анімацією під таймлайном
anim_frame = tk.Frame(center_container)
anim_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 5))

lbl_timeline = tk.Label(anim_frame, text=LANG_DATA["UA"]["lbl_timeline"], font=("Arial", 9, "bold"))
lbl_timeline.pack(side=tk.LEFT, padx=5)

# Контейнер із трьома кнопками керування по центру (▲, ✖, ↺)
ctrl_buttons_frame = tk.Frame(anim_frame)
ctrl_buttons_frame.pack(expand=True)

btn_play = tk.Button(ctrl_buttons_frame, text="▲", command=play_anim, bg="#e1edf8", font=("Arial", 11, "bold"), width=3)
btn_play.pack(side=tk.LEFT, padx=5)

btn_pause = tk.Button(ctrl_buttons_frame, text="✖", command=pause_anim, bg="#e1edf8", font=("Arial", 11, "bold"), width=3)
btn_pause.pack(side=tk.LEFT, padx=5)

btn_restart = tk.Button(ctrl_buttons_frame, text="↺", command=restart_anim, bg="#e1edf8", font=("Arial", 11, "bold"), width=3)
btn_restart.pack(side=tk.LEFT, padx=5)

root.mainloop()