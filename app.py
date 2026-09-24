import streamlit as st

st.set_page_config(
    page_title="Remex_v3",
    page_icon="🌱",
    layout="wide"
)

st.title("Remex_v3")
st.subheader("Модель біоремедіації нафтово забруднених ґрунтів")

st.write(
    "Інтерактивний вебінтерфейс для моделювання процесу "
    "біоремедіації ґрунтів."
)

st.divider()

st.header("Вхідні параметри")

col1, col2 = st.columns(2)

with col1:
    concentration = st.number_input(
        "Початкова концентрація нафтопродуктів, мг/кг",
        min_value=0.0,
        value=134000.0,
        step=1000.0
    )

    temperature = st.number_input(
        "Температура, °C",
        value=22.0,
        step=0.1
    )

with col2:
    humidity = st.number_input(
        "Вологість ґрунту, %",
        min_value=0.0,
        max_value=100.0,
        value=68.0,
        step=1.0
    )

    plant = st.selectbox(
        "Тип рослини",
        [
            "Сорго",
            "Просо",
            "Суміш сорго та проса",
            "Без рослин"
        ]
    )

st.divider()

if st.button("Розрахувати", type="primary"):

    st.success("Параметри отримано!")

    st.write("### Введені параметри")

    st.write(f"**Початкова концентрація:** {concentration:.0f} мг/кг")
    st.write(f"**Температура:** {temperature:.1f} °C")
    st.write(f"**Вологість:** {humidity:.0f} %")
    st.write(f"**Рослина:** {plant}")

    st.info(
        "Наступним кроком цей інтерфейс буде підключено "
        "безпосередньо до математичної моделі Remex_v3."
    )
