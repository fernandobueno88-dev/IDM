import streamlit as st
import pandas as pd
import re
from datetime import date

st.set_page_config(page_title="IDM Analytics", page_icon="🚛", layout="wide")

st.markdown("""
<style>
.card-geral {
    padding: 24px;
    border-radius: 18px;
    color: white;
    min-height: 330px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.12);
}
.verde { background: linear-gradient(135deg, #16a34a, #22c55e); }
.laranja { background: linear-gradient(135deg, #f59e0b, #f97316); }
.vermelho { background: linear-gradient(135deg, #dc2626, #ef4444); }

.titulo-card {
    font-size: 17px;
    font-weight: 700;
    margin-bottom: 20px;
}
.nota-card {
    font-size: 56px;
    font-weight: 900;
    margin-bottom: 8px;
}
.status-card {
    font-size: 21px;
    font-weight: 800;
    margin-bottom: 35px;
}
.detalhe-card {
    font-size: 14px;
    line-height: 1.7;
    margin-top: 18px;
}
.caixa-indicador {
    padding: 22px;
    border-radius: 16px;
    background: #f8fafc;
    border: 1px solid #e5e7eb;
    min-height: 125px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.indicador-titulo {
    font-size: 15px;
    color: #64748b;
}
.indicador-valor {
    font-size: 30px;
    font-weight: 800;
    color: #0f172a;
    margin-top: 8px;
}
</style>
""", unsafe_allow_html=True)

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


def classificar(nota):
    if nota >= 80:
        return "Bom"
    elif nota >= 60:
        return "Média"
    return "Pode ser melhorado"


def classe_cor(nota):
    if nota >= 80:
        return "verde"
    elif nota >= 60:
        return "laranja"
    return "vermelho"


def calcular_notas(row, media_consumo, media_km):
    km = row["Distância (Km)"]
    consumo = row["Km/l"]
    velocidade = row["Velocidade Máxima"]
    parado = row["Horas Parado"]
    conducao = row["Horas Condução"]

    economia = 100
    seguranca = 100
    velocidade_nota = 100
    parada = 100

    if consumo <= 0:
        economia -= 50
    elif media_consumo > 0 and consumo < media_consumo:
        economia -= 25

    if km <= 0:
        economia -= 30

    if media_km > 0 and km < media_km * 0.5:
        economia -= 15

    if velocidade > 80:
        seguranca -= 25
        velocidade_nota -= 30

    if velocidade > 90:
        seguranca -= 20
        velocidade_nota -= 20

    if parado > 4:
        parada -= 35

    if parado > 6:
        parada -= 25

    if conducao <= 0:
        parada -= 20

    economia = max(economia, 0)
    seguranca = max(seguranca, 0)
    velocidade_nota = max(velocidade_nota, 0)
    parada = max(parada, 0)

    nota_geral = round(
        (economia * 0.35)
        + (seguranca * 0.25)
        + (velocidade_nota * 0.20)
        + (parada * 0.20),
        0
    )

    return economia, seguranca, velocidade_nota, parada, nota_geral


def card_categoria(titulo, nota, detalhes):
    cor = classe_cor(nota)
    status = classificar(nota)

    detalhes_formatados = ""
    for item in detalhes:
        detalhes_formatados += f"<div>• {item}</div>"

    html = f"""
    <div class="card-geral {cor}">
        <div class="titulo-card">{titulo}</div>
        <div class="nota-card">{nota:.0f}</div>
        <div class="status-card">{status}</div>
        <hr style="border: 0.5px solid rgba(255,255,255,0.45);">
        <div class="detalhe-card">
            {detalhes_formatados}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def card_indicador(titulo, valor):
    html = f"""
    <div class="caixa-indicador">
        <div class="indicador-titulo">{titulo}</div>
        <div class="indicador-valor">{valor}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


if arquivo is not None:
    linha_cabecalho = encontrar_linha_cabecalho(arquivo)

    if linha_cabecalho is None:
        st.error("Não encontrei a linha do cabeçalho com Motorista.")
        st.stop()

    df = pd.read_excel(arquivo, header=linha_cabecalho)
    df.columns = [limpar_nome_coluna(c) for c in df.columns]

    col_motorista = encontrar_coluna(df, ["motorista"])
    col_distancia = encontrar_coluna(df, ["distância"])
    col_velocidade = encontrar_coluna(df, ["velocidade"])
    col_consumo = encontrar_coluna(df, ["km/l"])
    col_parado = encontrar_coluna(df, ["tempo", "parado"])
    col_conducao = encontrar_coluna(df, ["tempo", "condu"])
    col_litros = encontrar_coluna(df, ["litros"])
    col_co2 = encontrar_coluna(df, ["co2"])

    obrigatorias = {
        "Motorista": col_motorista,
        "Distância (Km)": col_distancia,
        "Velocidade Máxima": col_velocidade,
        "Km/l": col_consumo,
        "Tempo Parado": col_parado,
        "Tempo Condução": col_conducao
    }

    faltando = [nome for nome, coluna in obrigatorias.items() if coluna is None]

    if faltando:
        st.error("Colunas faltando:")
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

    if col_litros:
        renomear[col_litros] = "Litros"
    if col_co2:
        renomear[col_co2] = "CO2"

    df = df.rename(columns=renomear)

    df = df[df["Motorista"].notna()]
    df = df[df["Motorista"].astype(str).str.strip() != ""]

    df["Distância (Km)"] = pd.to_numeric(df["Distância (Km)"], errors="coerce").fillna(0)
    df["Velocidade Máxima"] = pd.to_numeric(df["Velocidade Máxima"], errors="coerce").fillna(0)
    df["Km/l"] = pd.to_numeric(df["Km/l"], errors="coerce").fillna(0)

    if "Litros" in df.columns:
        df["Litros"] = pd.to_numeric(df["Litros"], errors="coerce").fillna(0)
    else:
        df["Litros"] = 0

    if "CO2" in df.columns:
        df["CO2"] = pd.to_numeric(df["CO2"], errors="coerce").fillna(0)
    else:
        df["CO2"] = 0

    df["Horas Parado"] = df["Tempo Parado"].apply(tempo_para_horas)
    df["Horas Condução"] = df["Tempo Condução"].apply(tempo_para_horas)

    resumo = df.groupby("Motorista").agg({
        "Distância (Km)": "sum",
        "Km/l": "mean",
        "Velocidade Máxima": "max",
        "Horas Parado": "sum",
        "Horas Condução": "sum",
        "Litros": "sum",
        "CO2": "sum"
    }).reset_index()

    media_consumo = resumo[resumo["Km/l"] > 0]["Km/l"].mean()
    media_km = resumo[resumo["Distância (Km)"] > 0]["Distância (Km)"].mean()

    if pd.isna(media_consumo):
        media_consumo = 0
    if pd.isna(media_km):
        media_km = 0

    notas = resumo.apply(lambda row: calcular_notas(row, media_consumo, media_km), axis=1)

    resumo["Economia"] = [n[0] for n in notas]
    resumo["Segurança"] = [n[1] for n in notas]
    resumo["Velocidade"] = [n[2] for n in notas]
    resumo["Parada"] = [n[3] for n in notas]
    resumo["Nota IDM"] = [n[4] for n in notas]
    resumo["Classificação"] = resumo["Nota IDM"].apply(classificar)

    resumo = resumo.sort_values(by="Nota IDM", ascending=False)

    st.sidebar.header("🔎 Filtros")

    tipo_periodo = st.sidebar.radio("📅 Tipo de período", ["Dia", "Mês"])

    if tipo_periodo == "Dia":
        data_relatorio = st.sidebar.date_input("Escolha o dia", value=date.today())
        periodo_texto = data_relatorio.strftime("%d/%m/%Y")
    else:
        data_relatorio = st.sidebar.date_input("Escolha qualquer dia do mês", value=date.today())
        periodo_texto = data_relatorio.strftime("%m/%Y")

    motoristas = sorted(resumo["Motorista"].dropna().unique().tolist())
    motorista_selecionado = st.sidebar.selectbox("👤 Motorista", motoristas)

    dados_motorista = resumo[resumo["Motorista"] == motorista_selecionado]

    st.success("Arquivo processado com sucesso!")

    aba1, aba2, aba3 = st.tabs(["🚛 Painel do Motorista", "🏆 Ranking", "📋 Relatório"])

    with aba1:
        if dados_motorista.empty:
            st.warning("Motorista sem dados.")
        else:
            m = dados_motorista.iloc[0]

            st.subheader(f"🚛 {motorista_selecionado}")
            st.caption(f"Período selecionado: {periodo_texto}")

            col_geral, col1, col2, col3, col4 = st.columns([1.35, 1, 1, 1, 1])

            with col_geral:
                card_categoria(
                    "Pontuação IDM",
                    m["Nota IDM"],
                    [
                        "Diesel / Operação",
                        "80-100: Bom",
                        "60-79: Média",
                        "0-59: Pode ser melhorado"
                    ]
                )

            with col1:
                card_categoria(
                    "🛡️ Segurança",
                    m["Segurança"],
                    [
                        f"Velocidade máxima: {m['Velocidade Máxima']:.0f} km/h",
                        "Referência: até 80 km/h",
                        "Avalia condução segura"
                    ]
                )

            with col2:
                card_categoria(
                    "⛽ Economia",
                    m["Economia"],
                    [
                        f"Consumo: {m['Km/l']:.2f} km/l",
                        f"Média da frota: {media_consumo:.2f} km/l",
                        "Avalia eficiência no diesel"
                    ]
                )

            with col3:
                card_categoria(
                    "⚡ Velocidade",
                    m["Velocidade"],
                    [
                        f"Máxima: {m['Velocidade Máxima']:.0f} km/h",
                        "Acima de 80 km/h penaliza",
                        "Controle de excesso"
                    ]
                )

            with col4:
                card_categoria(
                    "🅿️ Parada",
                    m["Parada"],
                    [
                        f"Tempo parado: {horas_para_texto(m['Horas Parado'])}",
                        f"Tempo condução: {horas_para_texto(m['Horas Condução'])}",
                        "Avalia ociosidade"
                    ]
                )

            st.divider()

            st.subheader("📌 Indicadores do período")

            k1, k2, k3, k4, k5 = st.columns(5)

            with k1:
                card_indicador(
                    "Tempo total",
                    horas_para_texto(m["Horas Condução"] + m["Horas Parado"])
                )

            with k2:
                card_indicador(
                    "Distância total",
                    f'{m["Distância (Km)"]:,.2f} km'
                )

            with k3:
                velocidade_media = 0
                if m["Horas Condução"] > 0:
                    velocidade_media = m["Distância (Km)"] / m["Horas Condução"]

                card_indicador(
                    "Condução média",
                    f"{velocidade_media:.2f} km/h"
                )

            with k4:
                card_indicador(
                    "Consumo médio",
                    f'{m["Km/l"]:.2f} km/l'
                )

            with k5:
                if m["CO2"] > 0:
                    card_indicador("CO₂", f'{m["CO2"]:,.2f} kg')
                else:
                    card_indicador("CO₂", "-")

            st.divider()

            with st.expander("📂 Ver dados completos do motorista"):
                dados_motorista_original = df[df["Motorista"] == motorista_selecionado]
                st.dataframe(dados_motorista_original, use_container_width=True, hide_index=True)

    with aba2:
        st.subheader("🏆 Ranking IDM")

        r1, r2, r3, r4 = st.columns(4)

        r1.metric("Motoristas", resumo["Motorista"].nunique())
        r2.metric("KM Total", f'{resumo["Distância (Km)"].sum():,.0f} km')
        r3.metric("Consumo Médio", f'{media_consumo:.2f} km/l')
        r4.metric("Nota Média", f'{resumo["Nota IDM"].mean():.1f}')

        st.dataframe(resumo, use_container_width=True, hide_index=True)

        st.subheader("Top 10")
        st.bar_chart(resumo.head(10).set_index("Motorista")["Nota IDM"])

    with aba3:
        st.subheader("📋 Relatório completo")

        csv = resumo.to_csv(index=False).encode("utf-8-sig")

        st.download_button(
            label="📥 Baixar Ranking IDM",
            data=csv,
            file_name="ranking_idm.csv",
            mime="text/csv"
        )

        with st.expander("Abrir dados originais"):
            st.dataframe(df, use_container_width=True, hide_index=True)

else:
    st.warning("Aguardando envio do relatório.")
