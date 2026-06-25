import streamlit as st
import pandas as pd

st.set_page_config(page_title="IDM Analytics", page_icon="🚛", layout="wide")

st.title("🚛 IDM Analytics")
st.caption("Índice de Desempenho do Motorista")

arquivo = st.file_uploader("📁 Envie o relatório da Maxtrack", type=["xlsx"])

def tempo_para_horas(valor):
    try:
        if pd.isna(valor):
            return 0
        if isinstance(valor, str):
            partes = valor.split(":")
            if len(partes) >= 2:
                return int(partes[0]) + int(partes[1]) / 60
        return float(valor)
    except:
        return 0

def calcular_idm(row, media_consumo, media_km):
    nota = 100

    consumo = row.get("Km/l", 0)
    velocidade = row.get("Velocidade Máxima", 0)
    km = row.get("Distância (Km)", 0)
    tempo_parado = row.get("Horas Parado", 0)

    if consumo < media_consumo:
        nota -= 30

    if velocidade > 80:
        nota -= 20

    if tempo_parado > 4:
        nota -= 15

    if km < media_km * 0.5:
        nota -= 10

    if km <= 0 or consumo <= 0:
        nota -= 20

    return max(nota, 0)

def classificar(nota):
    if nota >= 90:
        return "Excelente 🟢"
    elif nota >= 80:
        return "Bom 🔵"
    elif nota >= 70:
        return "Atenção 🟡"
    elif nota >= 60:
        return "Ruim 🟠"
    else:
        return "Crítico 🔴"

if arquivo:
    bruto = pd.read_excel(arquivo, header=None)

linha_cabecalho = None

for i in range(len(bruto)):
    valores_linha = bruto.iloc[i].astype(str).str.strip().tolist()
    if "Motorista" in valores_linha:
        linha_cabecalho = i
        break

if linha_cabecalho is None:
    st.error("Não encontrei a linha do cabeçalho com a coluna Motorista.")
    st.dataframe(bruto.head(15))
    st.stop()

df = pd.read_excel(arquivo, header=linha_cabecalho)

    df.columns = df.columns.astype(str).str.strip()

    colunas_necessarias = [
        "Motorista",
        "Distância (Km)",
        "Velocidade Máxima",
        "Km/l",
        "Tempo Parado",
        "Tempo de Condução"
    ]

    faltando = [c for c in colunas_necessarias if c not in df.columns]

    if faltando:
        st.error("Algumas colunas não foram encontradas no relatório:")
        st.write(faltando)
        st.write("Colunas encontradas:")
        st.write(df.columns.tolist())
    else:
        df = df[df["Motorista"].notna()]

        df["Distância (Km)"] = pd.to_numeric(df["Distância (Km)"], errors="coerce").fillna(0)
        df["Velocidade Máxima"] = pd.to_numeric(df["Velocidade Máxima"], errors="coerce").fillna(0)
        df["Km/l"] = pd.to_numeric(df["Km/l"], errors="coerce").fillna(0)

        df["Horas Parado"] = df["Tempo Parado"].apply(tempo_para_horas)
        df["Horas Condução"] = df["Tempo de Condução"].apply(tempo_para_horas)

        resumo = df.groupby("Motorista").agg({
            "Distância (Km)": "sum",
            "Km/l": "mean",
            "Velocidade Máxima": "max",
            "Horas Parado": "sum",
            "Horas Condução": "sum"
        }).reset_index()

        media_consumo = resumo["Km/l"].mean()
        media_km = resumo["Distância (Km)"].mean()

        resumo["Nota IDM"] = resumo.apply(
            lambda row: calcular_idm(row, media_consumo, media_km),
            axis=1
        )

        resumo["Classificação"] = resumo["Nota IDM"].apply(classificar)

        resumo = resumo.sort_values(by="Nota IDM", ascending=False)

        st.subheader("📊 Dashboard Executivo")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Motoristas", resumo["Motorista"].nunique())
        col2.metric("KM Total", f'{resumo["Distância (Km)"].sum():,.0f} km')
        col3.metric("Consumo Médio", f'{media_consumo:.2f} km/l')
        col4.metric("Nota Média IDM", f'{resumo["Nota IDM"].mean():.1f}')

        st.divider()

        st.subheader("🏆 Ranking dos Motoristas")
        st.dataframe(
            resumo,
            use_container_width=True,
            hide_index=True
        )

        st.subheader("📈 Top 10 - Nota IDM")
        top10 = resumo.head(10).set_index("Motorista")
        st.bar_chart(top10["Nota IDM"])

        st.subheader("⛽ Consumo por Motorista")
        consumo = resumo.sort_values(by="Km/l", ascending=False).set_index("Motorista")
        st.bar_chart(consumo["Km/l"])

        st.subheader("🚛 KM Rodado por Motorista")
        km = resumo.sort_values(by="Distância (Km)", ascending=False).set_index("Motorista")
        st.bar_chart(km["Distância (Km)"])

        csv = resumo.to_csv(index=False).encode("utf-8-sig")

        st.download_button(
            label="📥 Baixar Ranking IDM",
            data=csv,
            file_name="ranking_idm.csv",
            mime="text/csv"
        )

        with st.expander("📋 Ver dados originais"):
            st.dataframe(df, use_container_width=True)

else:
    st.info("Envie o arquivo Excel da Maxtrack para gerar o IDM.")
