import mysql.connector
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# Menghubungkan ke database MySQL
conn = mysql.connector.connect(
    host="localhost", 
    user="root", 
    password="", 
    database="koi_farm1"
)

cursor = conn.cursor()
cursor.execute("SELECT temperature, ph, tds FROM sensor_data ORDER BY id DESC LIMIT 1")
data = cursor.fetchone()
temperature, ph, tds = data

# Definisi variabel fuzzy
temperature_var = ctrl.Antecedent(np.arange(15, 36, 1), 'temperature')
ph_var = ctrl.Antecedent(np.arange(4.0, 9.0, 0.1), 'ph')
tds_var = ctrl.Antecedent(np.arange(100, 500, 10), 'tds')
keran = ctrl.Consequent(np.arange(0, 2, 1), 'keran')

# Fungsi keanggotaan
temperature_var['rendah'] = fuzz.trimf(temperature_var.universe, [15, 15, 22])
temperature_var['normal'] = fuzz.trimf(temperature_var.universe, [20, 25, 30])
temperature_var['tinggi'] = fuzz.trimf(temperature_var.universe, [28, 35, 35])

ph_var['asam'] = fuzz.trimf(ph_var.universe, [4, 4, 6.5])
ph_var['netral'] = fuzz.trimf(ph_var.universe, [6, 7, 8])
ph_var['basa'] = fuzz.trimf(ph_var.universe, [7.5, 9, 9])

tds_var['rendah'] = fuzz.trimf(tds_var.universe, [100, 100, 200])
tds_var['normal'] = fuzz.trimf(tds_var.universe, [150, 250, 350])
tds_var['tinggi'] = fuzz.trimf(tds_var.universe, [300, 450, 500])

keran['mati'] = fuzz.trimf(keran.universe, [0, 0, 1])
keran['hidup'] = fuzz.trimf(keran.universe, [0, 1, 1])

# Aturan fuzzy
rule1 = ctrl.Rule(temperature_var['tinggi'] | tds_var['tinggi'] | ph_var['asam'], keran['hidup'])
rule2 = ctrl.Rule(temperature_var['normal'] & ph_var['netral'] & tds_var['normal'], keran['mati'])

keran_ctrl = ctrl.ControlSystem([rule1, rule2])
keran_simulasi = ctrl.ControlSystemSimulation(keran_ctrl)

# Input data dari sensor
keran_simulasi.input['temperature'] = temperature
keran_simulasi.input['ph'] = ph
keran_simulasi.input['tds'] = tds

# Hitung hasil
keran_simulasi.compute()

# Output
output_keran = keran_simulasi.output['keran']
print(f"Output keran: {output_keran}")

cursor.close()
conn.close()
