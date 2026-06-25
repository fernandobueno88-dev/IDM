import streamlit as st
import pandas as pd
import re

st.set_page_config(
    page_title="IDM Analytics",
    page_icon="🚛",
    layout="wide"
)

st.title("🚛 IDM Analytics")
st.caption("Índice de Desempenho do Motorista")

st.info("Envie o relatório Excel da Maxtrack para gerar o IDM.")

arquivo = st.file_uploader("📁 Envie o relatório da Maxtrack", type=["xlsx"])


def limpar_nome_coluna(nome):
    nome = str(nome).strip()
    nome = re.sub(r"\s+", " ", nome)
    return nome


def encontrar_linha_cabecalho(arquivo_excel):
    bruto = pd.read_excel(arquivo_excel, header=None)

    for i in range(len(bruto)):
        valores = bruto.iloc[i].astype(str).str.strip().tolist()

        if "Motorista" in valores:
            return i

    return None


def tempo_para_horas(valor):
    if pd.isna(valor):
        return 0

    texto = str(valor).lower().strip()

    horas = 0
    minutos = 0
    segundos = 0

    h = re.search(r"(\d+)\s*h", texto)
    m = re.search(r"(\d+)\s*m", texto)
    s = re.search(r"(\d+)\s*s", texto)

    if h:
        horas = int(h.group(1))
    if m:
        minutos = int(m.group(1))
    if s:
        segundos = int(s.group(1))

    return horas + minutos / 60 + segundos / 3600


def classificar_idm(nota):
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


def calcular_idm(row, media_consumo, media_km):
    nota = 100

    consumo = row["Km/l"]
    velocidade = row["Velocidade Máxima"]
    km = row["Distância (Km)"]
    parado = row["Horas Parado"]

    if km <= 0:
        nota -= 40

    if consumo <= 0:
        nota -= 30
    elif consumo < media_consumo:
        nota -= 20

    if velocidade > 80:
        nota -= 20

    if parado > 4:
        nota -= 10

    if km < media_km * 0.5:
        nota -= 10

    return max(nota, 0)


if arquivo is not None:
    linha_cabecalho = encontrar_linha_cabecalho(arquivo)

    if linha_cabecalho is None:
        st.error("Não consegui encontrar a linha do cabeçalho com a coluna Motorista.")
        st.stop()

    df = pd.read_excel(arquivo, header=linha_cabecalho)

    df.columns = [limpar_nome_coluna(c) for c in df.columns]

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
        st.error("Algumas colunas não foram encontradas no relatório.")
        st.write("Colunas faltando:")
        st.write(faltando)
        st.write("Colunas encontradas:")
        st.write(df.columns.tolist())
        st.stop()

    df = df[df["Motorista"].notna()]
    df = df[df["Motorista"].astype(str).str.strip() != ""]

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

    media_consumo = resumo[resumo["Km/l"] > 0]["Km/l"].mean()
    media_km = resumo[resumo["Distância (Km)"] > 0]["Distância (Km)"].mean()

    if pd.isna(media_consumo):
        media_consumo = 0

    if pd.isna(media_km):
        media_km = 0

    resumo["Nota IDM"] = resumo.apply(
        lambda row: calcular_idm(row, media_consumo, media_km),
        axis=1
    )

    resumo["Classificação"] = resumo["Nota IDM"].apply(classificar_idm)

    resumo = resumo.sort_values(by="Nota IDM", ascending=False)

    st.success("Arquivo processado com sucesso!")

    st.subheader("📊 Dashboard Executivo")

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Motoristas", resumo["Motorista"].nunique())
    col2.metric("KM Total", f'{resumo["Distância (Km)"].sum():,.0f} km')
    col3.metric("Consumo Médio", f"{media_consumo:.2f} km/l")
    col4.metric("Nota Média", f'{resumo["Nota IDM"].mean():.1f}')
    col5.metric("Velocidade Máxima", f'{resumo["Velocidade Máxima"].max():.0f} km/h')

    st.divider()

    st.subheader("🏆 Ranking IDM")
    st.dataframe(resumo, use_container_width=True, hide_index=True)

    st.subheader("📈 Top 10 Motoristas")
    top10 = resumo.head(10).set_index("Motorista")
    st.bar_chart(top10["Nota IDM"])

    st.subheader("⛽ Consumo por Motorista")
    consumo = resumo.sort_values(by="Km/l", ascending=False).set_index("Motorista")
    st.bar_chart(consumo["Km/l"])

    st.subheader("🚛 KM Rodado por Motorista")
    km = resumo.sort_values(by="Distância (Km)", ascending=False).set_index("Motorista")
    st.bar_chart(km["Distância (Km)"])

    st.subheader("🕒 Tempo Parado por Motorista")
    parado = resumo.sort_values(by="Horas Parado", ascending=False).set_index("Motorista")
    st.bar_chart(parado["Horas Parado"])

    csv = resumo.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label="📥 Baixar Ranking IDM em CSV",
        data=csv,
        file_name="ranking_idm.csv",
        mime="text/csv"
    )

    with st.expander("📋 Ver dados originais"):
        st.dataframe(df, use_container_width=True)

else:
    st.warning("Aguardando envio do relatório.")
