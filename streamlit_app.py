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


def horas_para_texto(horas):
    h = int(horas)
    m = int((horas - h) * 60)
    return f"{h}h {m}min"


def classificar_idm(nota):
    if nota >= 90:
        return "Excelente"
    elif nota >= 80:
        return "Bom"
    elif nota >= 70:
        return "Atenção"
    elif nota >= 60:
        return "Ruim"
    else:
        return "Crítico"


def cor_nota(nota):
    if nota >= 90:
        return "#16a34a"
    elif nota >= 80:
        return "#2563eb"
    elif nota >= 70:
        return "#facc15"
    elif nota >= 60:
        return "#f97316"
    else:
        return "#dc2626"


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
    cor = cor_nota(nota)

    html = f"""
    <div style="display:flex; justify-content:center; align-items:center;">
        <div style="
            width:230px;
            height:230px;
            border-radius:50%;
            background: conic-gradient({cor} {nota * 3.6}deg, #e5e7eb 0deg);
            display:flex;
            align-items:center;
            justify-content:center;
            box-shadow: 0 4px 22px rgba(0,0,0,0.18);
        ">
            <div style="
                width:165px;
                height:165px;
                border-radius:50%;
                background:white;
                display:flex;
                flex-direction:column;
                align-items:center;
                justify-content:center;
            ">
                <div style="font-size:46px; font-weight:900; color:{cor};">{nota:.0f}</div>
                <div style="font-size:16px; color:#555;">Nota IDM</div>
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def card(titulo, valor, subtitulo=""):
    st.markdown(
        f"""
        <div style="
            padding:18px;
            border-radius:14px;
            background:#f8fafc;
            border:1px solid #e5e7eb;
            box-shadow:0 2px 8px rgba(0,0,0,0.05);
            min-height:120px;
        ">
            <div style="font-size:15px; color:#64748b;">{titulo}</div>
            <div style="font-size:32px; font-weight:800; color:#0f172a; margin-top:8px;">{valor}</div>
            <div style="font-size:13px; color:#64748b; margin-top:6px;">{subtitulo}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def barra_indicador(nome, valor, maximo, unidade=""):
    percentual = 0
    if maximo > 0:
        percentual = min((valor / maximo) * 100, 100)

    st.markdown(
        f"""
        <div style="margin-bottom:18px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
                <span style="font-weight:700;">{nome}</span>
                <span>{valor:.2f} {unidade}</span>
            </div>
            <div style="width:100%; height:16px; background:#e5e7eb; border-radius:20px;">
                <div style="width:{percentual}%; height:16px; background:#16a34a; border-radius:20px;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


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

    st.sidebar.header("🔎 Filtros")

    data_relatorio = st.sidebar.date_input(
        "📅 Data do relatório",
        value=date.today()
    )

    motoristas = sorted(resumo["Motorista"].dropna().unique().tolist())
    motorista_selecionado = st.sidebar.selectbox("👤 Motorista", motoristas)

    dados_motorista = resumo[resumo["Motorista"] == motorista_selecionado]

    st.success("Arquivo processado com sucesso!")

    aba1, aba2, aba3 = st.tabs(["👤 Motorista", "🏆 Ranking", "📋 Relatório Completo"])

    with aba1:
        if dados_motorista.empty:
            st.warning("Motorista sem dados.")
        else:
            m = dados_motorista.iloc[0]

            nota = m["Nota IDM"]
            classificacao = m["Classificação"]
            cor = cor_nota(nota)

            st.subheader(f"👤 {motorista_selecionado}")
            st.caption(f"Data do relatório: {data_relatorio.strftime('%d/%m/%Y')}")

            col_nota, col_cards = st.columns([1, 2.4])

            with col_nota:
                indicador_circular(nota)
                st.markdown(
                    f"""
                    <h2 style="text-align:center; color:{cor}; margin-top:20px;">
                        {classificacao}
                    </h2>
                    """,
                    unsafe_allow_html=True
                )

            with col_cards:
                c1, c2, c3 = st.columns(3)
                with c1:
                    card("🚛 KM Rodado", f'{m["Distância (Km)"]:,.0f} km')
                with c2:
                    card("⛽ Consumo", f'{m["Km/l"]:.2f} km/l')
                with c3:
                    card("⚡ Velocidade Máxima", f'{m["Velocidade Máxima"]:.0f} km/h')

                c4, c5, c6 = st.columns(3)
                with c4:
                    card("🕒 Tempo Parado", horas_para_texto(m["Horas Parado"]))
                with c5:
                    card("🛣️ Tempo Condução", horas_para_texto(m["Horas Condução"]))
                with c6:
                    card("⭐ Nota IDM", f'{m["Nota IDM"]:.0f}', classificacao)

            st.divider()

            st.subheader("📊 Indicadores do Motorista")

            max_km = resumo["Distância (Km)"].max()
            max_consumo = resumo["Km/l"].max()
            max_parado = resumo["Horas Parado"].max()
            max_conducao = resumo["Horas Condução"].max()

            barra_indicador("KM Rodado", m["Distância (Km)"], max_km, "km")
            barra_indicador("Consumo", m["Km/l"], max_consumo, "km/l")
            barra_indicador("Tempo Condução", m["Horas Condução"], max_conducao, "h")
            barra_indicador("Tempo Parado", m["Horas Parado"], max_parado, "h")

            st.divider()

            st.subheader("📌 Resumo fácil de ler")

            resumo_facil = pd.DataFrame({
                "Indicador": [
                    "Motorista",
                    "Data do relatório",
                    "Nota IDM",
                    "Classificação",
                    "KM Rodado",
                    "Consumo",
                    "Velocidade Máxima",
                    "Tempo Parado",
                    "Tempo Condução"
                ],
                "Resultado": [
                    motorista_selecionado,
                    data_relatorio.strftime("%d/%m/%Y"),
                    f'{m["Nota IDM"]:.0f}',
                    classificacao,
                    f'{m["Distância (Km)"]:,.0f} km',
                    f'{m["Km/l"]:.2f} km/l',
                    f'{m["Velocidade Máxima"]:.0f} km/h',
                    horas_para_texto(m["Horas Parado"]),
                    horas_para_texto(m["Horas Condução"])
                ]
            })

            st.dataframe(resumo_facil, use_container_width=True, hide_index=True)

            with st.expander("📂 Ver dados completos deste motorista"):
                dados_filtrados_motorista = df[df["Motorista"] == motorista_selecionado]
                st.dataframe(dados_filtrados_motorista, use_container_width=True, hide_index=True)

    with aba2:
        st.subheader("🏆 Ranking IDM")

        col1, col2, col3, col4, col5 = st.columns(5)

        col1.metric("Motoristas", resumo["Motorista"].nunique())
        col2.metric("KM Total", f'{resumo["Distância (Km)"].sum():,.0f} km')
        col3.metric("Consumo Médio", f"{media_consumo:.2f} km/l")
        col4.metric("Nota Média", f'{resumo["Nota IDM"].mean():.1f}')
        col5.metric("Maior Velocidade", f'{resumo["Velocidade Máxima"].max():.0f} km/h')

        st.divider()

        st.dataframe(resumo, use_container_width=True, hide_index=True)

        st.subheader("📈 Top 10 Motoristas")
        top10 = resumo.head(10).set_index("Motorista")
        st.bar_chart(top10["Nota IDM"])

    with aba3:
        st.subheader("📋 Relatório completo")

        with st.expander("📂 Abrir dados originais"):
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
