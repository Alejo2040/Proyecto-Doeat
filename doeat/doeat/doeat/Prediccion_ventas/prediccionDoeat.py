import pandas as pd
import numpy as np
import json
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

# === 1. Cargar datos desde Excel ===
archivo_excel = "doeat/doeat/Prediccion_ventas/doeat_ventas_simulado.xlsx"
df = pd.read_excel(archivo_excel, sheet_name="Detalles", engine="openpyxl")

# === 2. Preprocesar fechas y columnas ===
df["Fecha de creación"] = df["Fecha de creación"].astype(str).str.split("|").str[0].str.strip()
df["Fecha de creación"] = pd.to_datetime(df["Fecha de creación"], format="%d/%m/%Y", errors="coerce")

df = df.rename(columns={
    "Fecha de creación": "fecha_venta",
    "Nombre del producto": "producto",
    "Cantidad": "cantidad_vendida"
})

# === 3. Agregar ventas por fecha y producto ===
ventas = df.groupby(['fecha_venta', 'producto'])['cantidad_vendida'].sum().reset_index()

# === 4. Pivotear para crear series temporales por producto ===
pivot = ventas.pivot(index='fecha_venta', columns='producto', values='cantidad_vendida').fillna(0)

# === 5. Función de ingeniería de características ===
def create_features(serie, lags=[1, 7], windows=[7]):
    df_feat = pd.DataFrame(index=serie.index)
    df_feat['target'] = serie
    for lag in lags:
        df_feat[f'lag_{lag}'] = serie.shift(lag)
    for window in windows:
        df_feat[f'rolling_mean_{window}'] = serie.shift(1).rolling(window=window).mean()
    df_feat['dia_semana'] = serie.index.dayofweek
    df_feat['dia_del_anio'] = serie.index.dayofyear
    return df_feat.dropna()

# === 6. Procesar y predecir por producto ===
resultados = []
predicciones_excel = []

for producto in pivot.columns:
    serie = pivot[producto]
    data = create_features(serie)

    if len(data) < 10:
        print(f"[INFO] Producto '{producto}' omitido: datos insuficientes.")
        continue

    X = data.drop(columns=['target'])
    y = data['target']

    X_train, X_test, y_train, y_test = train_test_split(X, y, shuffle=False, test_size=0.2)

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    ultimos_datos = data.iloc[-1:].drop(columns=['target'])
    prediccion = model.predict(ultimos_datos)[0]
    mse = mean_squared_error(y_test, model.predict(X_test))

    fecha_prediccion = data.index[-1] + pd.Timedelta(days=1)
    
    resultado = {
        "producto": producto,
        "fecha_prediccion": fecha_prediccion.strftime("%Y-%m-%d"),
        "cantidad_predicha": round(prediccion, 2),
        "mse_modelo": round(mse, 2)
    }
    resultados.append(resultado)
    predicciones_excel.append({
        "Producto": producto,
        "Fecha predicción": fecha_prediccion,
        "Cantidad predicha": round(prediccion, 2),
        "MSE": round(mse, 2)
    })

    print(f"[OK] {producto} → {round(prediccion, 2)} (MSE: {round(mse, 2)})")

# === 7. Guardar en JSON ===
with open("prediccion_mes.json", "w", encoding="utf-8") as f:
    json.dump(resultados, f, ensure_ascii=False, indent=4)

# === 8. Guardar en Excel (más visual) ===
df_salida = pd.DataFrame(predicciones_excel)
df_salida.to_excel("prediccion_stock_diario.xlsx", index=False)

print("\n✅ Predicciones completadas y guardadas.")
