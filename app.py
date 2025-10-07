from flask import Flask, render_template, request, redirect, send_file
import pandas as pd
from fpdf import FPDF
import os

app = Flask(__name__)

EXCEL_FILE = 'inventario.xlsx'

# Crear archivo si no existe
if not os.path.exists(EXCEL_FILE):
    df = pd.DataFrame(columns=['Código', 'Producto', 'Cantidad', 'Cantidad Real'])
    df.to_excel(EXCEL_FILE, index=False)

def leer_df():
    df = pd.read_excel(EXCEL_FILE)
    if 'Cantidad' not in df.columns:
        df['Cantidad'] = 0
    else:
        df['Cantidad'] = pd.to_numeric(df['Cantidad'], errors='coerce').fillna(0).astype(int)
    if 'Cantidad Real' not in df.columns:
        df['Cantidad Real'] = 0
    else:
        df['Cantidad Real'] = pd.to_numeric(df['Cantidad Real'], errors='coerce').fillna(0).astype(int)
    return df

def guardar_df(df):
    df.to_excel(EXCEL_FILE, index=False)

@app.route('/')
def index():
    df = leer_df()
    records = df.to_dict(orient='records')
    return render_template('index.html', tables=records)

@app.route('/actualizar', methods=['POST'])
def actualizar():
    codigo = request.form.get('codigo', '').strip()
    nombre = request.form.get('nombre', '').strip()
    try:
        cantidad = int(request.form.get('cantidad', '0'))
    except ValueError:
        cantidad = 0
    tipo = request.form.get('tipo')
    accion = request.form.get('accion')

    if codigo == '':
        return redirect('/')

    df = leer_df()
    mask = df['Código'].astype(str) == codigo

    if mask.any():
        idx = df.index[mask][0]
        if tipo == 'sistema':
            df.at[idx, 'Cantidad'] = max(0, df.at[idx, 'Cantidad'] + cantidad if accion=='sumar' else df.at[idx, 'Cantidad'] - cantidad)
        else:
            df.at[idx, 'Cantidad Real'] = max(0, df.at[idx, 'Cantidad Real'] + cantidad if accion=='sumar' else df.at[idx, 'Cantidad Real'] - cantidad)
        if nombre:
            df.at[idx, 'Producto'] = nombre
    else:
        nuevo = {
            'Código': codigo,
            'Producto': nombre if nombre else 'Nuevo producto',
            'Cantidad': cantidad if tipo=='sistema' and accion=='sumar' else 0,
            'Cantidad Real': cantidad if tipo=='real' and accion=='sumar' else 0
        }
        df = pd.concat([df, pd.DataFrame([nuevo])], ignore_index=True)

    guardar_df(df)
    return redirect('/')

@app.route('/editar_nombre', methods=['POST'])
def editar_nombre():
    codigo = request.form.get('codigo', '').strip()
    nuevo_nombre = request.form.get('nombre', '').strip()
    if codigo and nuevo_nombre:
        df = leer_df()
        mask = df['Código'].astype(str) == codigo
        if mask.any():
            idx = df.index[mask][0]
            df.at[idx, 'Producto'] = nuevo_nombre
            guardar_df(df)
    return redirect('/')

@app.route('/pasar_real_a_fisico', methods=['POST'])
def pasar_real_a_fisico():
    df = leer_df()
    df['Cantidad'] = df['Cantidad Real'].astype(int)
    df['Cantidad Real'] = 0
    guardar_df(df)
    return redirect('/')

@app.route('/exportar_pdf', methods=['POST'])
def exportar_pdf():
    df = leer_df()
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Reporte de Inventario", ln=True, align="C")
    pdf.ln(4)

    pdf.set_font("Arial", "B", 11)
    pdf.cell(40, 10, "Código", 1, 0, 'C')
    pdf.cell(80, 10, "Producto", 1, 0, 'C')
    pdf.cell(35, 10, "Cantidad", 1, 0, 'C')
    pdf.cell(35, 10, "Cantidad Real", 1, 1, 'C')

    pdf.set_font("Arial", "", 10)
    for _, row in df.iterrows():
        pdf.cell(40, 8, str(row['Código']), 1, 0, 'C')
        pdf.cell(80, 8, str(row['Producto'])[:40], 1, 0, 'L')
        pdf.cell(35, 8, str(int(row['Cantidad'])), 1, 0, 'C')
        pdf.cell(35, 8, str(int(row['Cantidad Real'])), 1, 1, 'C')

    out_path = "inventario.pdf"
    pdf.output(out_path)
    return send_file(out_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
