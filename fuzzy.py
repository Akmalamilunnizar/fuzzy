import mysql.connector
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import numpy as np

# Connect to the MySQL database
conn = mysql.connector.connect(
    host="localhost", 
    user="root", 
    password="", 
    database="koi_farm1"
)

cursor = conn.cursor()

# Fetch the latest sensor data and the related pond_id
cursor.execute("SELECT pond_id, temperature, ph, tds FROM sensor ORDER BY id_sensor DESC LIMIT 1")
data = cursor.fetchone()

if data:
    pond_id, temperature, ph, tds = data

    # Debug: Print fetched data
    print(f"Fetched Data - Pond ID: {pond_id}, Temperature: {temperature}, pH: {ph}, TDS: {tds}")

    # Define fuzzy variables
    temperature_var = ctrl.Antecedent(np.arange(10, 40, 1), 'temperature')  # Expanded range
    ph_var = ctrl.Antecedent(np.arange(3.0, 10.0, 0.1), 'ph')              # Expanded range
    tds_var = ctrl.Antecedent(np.arange(50, 600, 10), 'tds')               # Expanded range
    keran = ctrl.Consequent(np.arange(0, 2, 1), 'keran')

    # Membership functions
    temperature_var['rendah'] = fuzz.trimf(temperature_var.universe, [10, 15, 22])
    temperature_var['normal'] = fuzz.trimf(temperature_var.universe, [20, 25, 30])
    temperature_var['tinggi'] = fuzz.trimf(temperature_var.universe, [28, 35, 40])

    ph_var['asam'] = fuzz.trimf(ph_var.universe, [3.0, 4.0, 6.5])
    ph_var['netral'] = fuzz.trimf(ph_var.universe, [6.0, 7.0, 8.0])
    ph_var['basa'] = fuzz.trimf(ph_var.universe, [7.5, 9.0, 10.0])

    tds_var['rendah'] = fuzz.trimf(tds_var.universe, [50, 100, 200])
    tds_var['normal'] = fuzz.trimf(tds_var.universe, [150, 250, 350])
    tds_var['tinggi'] = fuzz.trimf(tds_var.universe, [300, 450, 600])

    keran['mati'] = fuzz.trimf(keran.universe, [0, 0, 1])
    keran['hidup'] = fuzz.trimf(keran.universe, [0, 1, 1])

    # Define fuzzy rules
    rule1 = ctrl.Rule(temperature_var['tinggi'] | tds_var['tinggi'] | ph_var['asam'], keran['hidup'])
    rule2 = ctrl.Rule(temperature_var['normal'] & ph_var['netral'] & tds_var['normal'], keran['mati'])
    rule3 = ctrl.Rule(temperature_var['rendah'] & tds_var['rendah'], keran['mati'])
    rule4 = ctrl.Rule(ph_var['basa'], keran['hidup'])

    # Corrected "always-true" default rule
    rule_default = ctrl.Rule(temperature_var['rendah'] | temperature_var['normal'] | temperature_var['tinggi'], keran['mati'])

    # Add rules to the control system
    keran_ctrl = ctrl.ControlSystem([rule1, rule2, rule3, rule4, rule_default])
    keran_simulasi = ctrl.ControlSystemSimulation(keran_ctrl)

    # Ensure the input values are within the defined ranges
    print(f"Input Data - Temperature: {temperature}, pH: {ph}, TDS: {tds}")
    temperature = max(10, min(temperature, 40))  # Clamp to range 10-40
    ph = max(3.0, min(ph, 10.0))                 # Clamp to range 3.0-10.0
    tds = max(50, min(tds, 600))                 # Clamp to range 50-600

    # Input sensor data into the fuzzy system
    keran_simulasi.input['temperature'] = temperature
    keran_simulasi.input['ph'] = ph
    keran_simulasi.input['tds'] = tds

    # Compute the fuzzy output
    try:
        keran_simulasi.compute()
        output_keran = keran_simulasi.output['keran']
        print(f"Fuzzy Output (Keran): {output_keran}")

        # Determine relay condition
        relay_condition = 1 if output_keran > 0.5 else 0

        # Update the relay_condition in the ponds table
        cursor.execute("UPDATE ponds SET relay_condition = %s WHERE id = %s", (relay_condition, pond_id))
        conn.commit()
        print(f"Relay condition for pond_id {pond_id} updated to: {relay_condition}")
    except Exception as e:
        print(f"Error during computation: {e}")
else:
    print("No sensor data found.")

# Close the database connection
cursor.close()
conn.close()
