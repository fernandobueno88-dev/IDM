import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="IDM Analytics",
    page_icon="🚛",
    layout="wide"
)

st.title("🚛 IDM Analytics")
st.subheader("Índice de Desempenho do Motorista")

st.info("Envie o relatório da Maxtrack em Excel para gerar a nota dos motoristas.")

arquivo = st.file_uploader("📁 Envie o arquivo Excel da Maxtrack", type=["xlsx"])

if arquivo is not None:
    df = pd.read_excel(arquivo)

    st.success("Arquivo carregado com sucesso!")

    st.write("### Prévia dos dados")
    st.dataframe(df)

    st.write("### Colunas encontradas no arquivo")
    st.write(df.columns.tolist())

    st.divider()

    st.write("## 📊 Indicador IDM")

    # Aqui vamos ajustar os nomes das colunas conforme o relatório real
    coluna_motorista = st.selectbox("Selecione a coluna do motorista", df.columns)
    coluna_km = st.selectbox("Selecione a coluna de KM rodado", df.columns)
    coluna_consumo = st.selectbox("Selecione a coluna de consumo ou média", df.columns)

    if st.button("Gerar Indicador"):
        resultado = df.groupby(coluna_motorista).agg({
            coluna_km: "sum",
            coluna_consumo: "mean"
        }).reset_index()

        resultado.columns = ["Motorista", "KM Rodado", "Média/Consumo"]

        resultado["Nota IDM"] = 100

        resultado.loc[resultado["Média/Consumo"] < resultado["Média/Consumo"].mean(), "Nota IDM"] -= 20

        resultado["Classificação"] = resultado["Nota IDM"].apply(
            lambda nota: "Excelente" if nota >= 90 else
            "Bom" if nota >= 80 else
            "Atenção" if nota >= 60 else
            "Crítico"
        )

        st.write("### Resultado por Motorista")
        st.dataframe(resultado)

        st.write("### Ranking IDM")
        ranking = resultado.sort_values(by="Nota IDM", ascending=False)
        st.dataframe(ranking)

        st.download_button(
            label="📥 Baixar resultado em Excel",
            data=ranking.to_csv(index=False).encode("utf-8"),
            file_name="resultado_idm.csv",
            mime="text/csv"
        )

else:
    st.warning("Aguardando envio do arquivo.")
