import streamlit as st

"""Informatiepagina over dit project en de ontwikkelgroep"""

st.set_page_config(
    page_title="Over deze applicatie | Longkanker CDSS",
    page_icon="🫁",
    layout="wide",
)

st.title("Op deze pagina vindt u meer informatie over dit project en het ontwikkelteam")

# Create containers to show information cleanly
project = st.container()
team = st.container()

with project:
    st.header("Informatie over dit CDSS")
    st.caption("Dit Clinical Decision Support System (CDSS) voor Non Small Cell Lung Cancer (NSCLC) is gebouwd op basis van syntetische data van IKNL. \n"
               "Met behulp van deze data is er een Neuraal Netwerk (NN) getraind om de 5-jaar overlevingskans van patiënten te schatten "
               "op basis van de gegeven patiënt- en tumorkenmerken.\n"
               "Daarnaast is er gebruik gemaakt van de richtlijn Criteria voor medische (in)operabiliteit"
               " voor NSCLC-patiënten om informatie te kunnen verstrekken over resectie mogelijkheden bij een gegeven patiënt.\n"
               "\nMeer informatie over IKNL is te vinden op hun website: \n"
               "https://iknl.nl/ \n"
               "\nDe gebruikte richtlijn is te vinden op: \n"
               "https://richtlijnendatabase.nl/richtlijn/niet_kleincellig_longcarcinoom/niet_kleincellig_longcarcinoom.html")

with team:
    st.header("Informatie over dit project en de ontwikkelgroep")
    st.caption("Dit CDSS is ontwikkeld als project voor het derdejaars bachelorvak 3.1: Artificiële Intelligentie van de studie Medische Informatiekunde"
               "aan de Universiteit van Amsterdam (UVA).\n"
               "Dit CDSS is ontwikkeld voor de gebruikersgroep 'specialisten' (oncologen) door projectgroep 5 bestaande uit:\n"
               "\nElsa Korte\n \nAlbert Segers\n \nKaj Dirks\n")

# Navigation
st.divider()

if st.button(
    "Terug naar Homepagina",
    use_container_width=True,
):
    st.switch_page("Home.py")