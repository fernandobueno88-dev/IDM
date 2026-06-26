import streamlit as st
import pandas as pd
import re
from datetime import date

st.set_page_config(page_title="IDM Analytics", page_icon="🚛", layout="wide")

st.title("🚛 IDM Analytics")
st.caption("Índice de Desempenho do Motorista")

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


def indicador_circular(nota):
    cor = "#16a34a"
    if nota < 90:
        cor = "#2563eb"
    if nota < 80:
        cor = "#facc15"
    if nota < 70:
        cor = "#f97316"
    if nota < 60:
        cor = "#dc2626"

    html = f"""
    <div style="display:flex; justify-content:center; align-items:center;">
        <div style="
            width:220px;
            height:220px;
            border-radius:50%;
            background: conic-gradient({cor} {nota * 3.6}deg, #e5e7eb 0deg);
            display:flex;
            align-items:center;
            justify-content:center;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        ">
            <div style="
                width:160px;
                height:160px;
                border-radius:50%;
                background:white;
                display:flex;
                flex-direction:column;
                align-items:center;
                justify-content:center;
            ">
                <div style="font-size:42px; font-weight:800; color:{cor};">{nota:.0f}</div>
                <div style="font-size:16px; color:#555;">Nota IDM</div>
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


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
    col_data = encontrar_coluna(df, ["data"])

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

    renomear = {
        col_motorista: "Motorista",
        col_distancia: "Distância (Km)",
        col_velocidade: "Velocidade Máxima",
        col_consumo: "Km/l",
        col_parado: "Tempo Parado",
        col_conducao: "Tempo Condução"
    }

    if col_data is not None:
        renomear[col_data] = "Data"

    df = df.rename(columns=renomear)

    df = df[df["Motorista"].notna()]
    df = df[df["Motorista"].astype(str).str.strip() != ""]

    df["Distância (Km)"] = pd.to_numeric(df["Distância (Km)"], errors="coerce").fillna(0)
    df["Velocidade Máxima"] = pd.to_numeric(df["Velocidade Máxima"], errors="coerce").fillna(0)
    df["Km/l"] = pd.to_numeric(df["Km/l"], errors="coerce").fillna(0)

    df["Horas Parado"] = df["Tempo Parado"].apply(tempo_para_horas)
    df["Horas Condução"] = df["Tempo Condução"].apply(tempo_para_horas)

    if "Data" in df.columns:
        df["Data"] = pd.to_datetime(df["Data"], errors="coerce").dt.date

    st.sidebar.header("🔎 Filtros")

    motoristas = sorted(df["Motorista"].dropna().unique().tolist())
    motorista_selecionado = st.sidebar.selectbox("Motorista", motoristas)

    if "Data" in df.columns and df["Data"].notna().any():
        data_min = df["Data"].min()
        data_max = df["Data"].max()

        intervalo_data = st.sidebar.date_input(
            "Período",
            value=(data_min, data_max),
            min_value=data_min,
            max_value=data_max
        )

        if isinstance(intervalo_data, tuple) and len(intervalo_data) == 2:
            inicio, fim = intervalo_data
            df = df[(df["Data"] >= inicio) & (df["Data"] <= fim)]
    else:
        st.sidebar.info("Este relatório não trouxe uma coluna de data identificável.")

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

    dados_motorista = resumo[resumo["Motorista"] == motorista_selecionado]

    st.success("Arquivo processado com sucesso!")

    aba1, aba2, aba3 = st.tabs(["👤 Motorista", "📊 Dashboard Geral", "📋 Dados"])

    with aba1:
        if dados_motorista.empty:
            st.warning("Motorista sem dados no período selecionado.")
        else:
            m = dados_motorista.iloc[0]

            st.subheader(f"👤 {motorista_selecionado}")

            col_nota, col_info = st.columns([1, 2])

            with col_nota:
                indicador_circular(m["Nota IDM"])
                st.markdown(
                    f"<h3 style='text-align:center'>{m['Classificação']}</h3>",
                    unsafe_allow_html=True
                )

            with col_info:
                c1, c2, c3 = st.columns(3)
                c1.metric("KM Rodado", f'{m["Distância (Km)"]:,.0f} km')
                c2.metric("Consumo", f'{m["Km/l"]:.2f} km/l')
                c3.metric("Velocidade Máxima", f'{m["Velocidade Máxima"]:.0f} km/h')

                c4, c5, c6 = st.columns(3)
                c4.metric("Tempo Parado", f'{m["Horas Parado"]:.1f} h')
                c5.metric("Tempo Condução", f'{m["Horas Condução"]:.1f} h')
                c6.metric("Nota IDM", f'{m["Nota IDM"]:.0f}')

            st.divider()

            st.subheader("📌 Detalhamento do motorista")
            dados_filtrados_motorista = df[df["Motorista"] == motorista_selecionado]
            st.dataframe(dados_filtrados_motorista, use_container_width=True, hide_index=True)

    with aba2:
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

    with aba3:
        st.subheader("📋 Dados Originais")
        st.dataframe(df, use_container_width=True, hide_index=True)

        csv = resumo.to_csv(index=False).encode("utf-8-sig")

        st.download_button(
            label="📥 Baixar Ranking IDM em CSV",
            data=csv,
            file_name="ranking_idm.csv",
            mime="text/csv"
        )

else:
    st.warning("Aguardando envio do relatório.")
