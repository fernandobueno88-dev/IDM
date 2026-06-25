import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="IDM Analytics", page_icon="🚛", layout="wide")

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


def encontrar_coluna(df, palavras):
    for coluna in df.columns:
        nome = str(coluna).lower()
        if all(p.lower() in nome for p in palavras):
            return coluna
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

    if media_km > 0 and km < media_km * 0.5:
        nota -= 10

    return max(nota, 0)


if arquivo is not None:
    linha_cabecalho = encontrar_linha_cabecalho(arquivo)

    if linha_cabecalho is None:
        st.error("Não consegui encontrar a linha do cabeçalho com a coluna Motorista.")
        st.stop()

    df = pd.read_excel(arquivo, header=linha_cabecalho)
    df.columns = [limpar_nome_coluna(c) for c in df.columns]

    col_motorista = encontrar_coluna(df, ["motorista"])
    col_distancia = encontrar_coluna(df, ["distância"])
    col_velocidade = encontrar_coluna(df, ["velocidade"])
    col_consumo = encontrar_coluna(df, ["km/l"])
    col_parado = encontrar_coluna(df, ["tempo", "parado"])
    col_conducao = encontrar_coluna(df, ["tempo", "condu"])

    colunas = {
        "Motorista": col_motorista,
        "Distância (Km)": col_distancia,
        "Velocidade Máxima": col_velocidade,
        "Km/l": col_consumo,
        "Tempo Parado": col_parado,
        "Tempo Condução": col_conducao
    }

    faltando = [nome for nome, coluna in colunas.items() if coluna is None]

    if faltando:
        st.error("Algumas colunas não foram encontradas no relatório.")
        st.write("Colunas faltando:")
        st.write(faltando)
        st.write("Colunas encontradas:")
        st.write(df.columns.tolist())
        st.stop()

    df = df.rename(columns={
        col_motorista: "Motorista",
        col_distancia: "Distância (Km)",
        col_velocidade: "Velocidade Máxima",
        col_consumo: "Km/l",
        col_parado: "Tempo Parado",
        col_conducao: "Tempo Condução"
    })

    df = df[df["Motorista"].notna()]
    df = df[df["Motorista"].astype(str).str.strip() != ""]

    df["Distância (Km)"] = pd.to_numeric(df["Distância (Km)"], errors="coerce").fillna(0)
    df["Velocidade Máxima"] = pd.to_numeric(df["Velocidade Máxima"], errors="coerce").fillna(0)
    df["Km/l"] = pd.to_numeric(df["Km/l"], errors="coerce").fillna(0)

    df["Horas Parado"] = df["Tempo Parado"].apply(tempo_para_horas)
    df["Horas Condução"] = df["Tempo Condução"].apply(tempo_para_horas)

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
