import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# -------------------
# 🔹 COOKIE de Hiper Olivos
# -------------------
COOKIE_SEGMENT = "eyJjYW1wYWlnbnMiOm51bGwsImNoYW5uZWwiOiIxIiwicHJpY2VUYWJsZXMiOm51bGwsInJlZ2lvbklkIjpudWxsLCJ1dG1fY2FtcGFpZ24iOm51bGwsInV0bV9zb3VyY2UiOm51bGwsInV0bWlfY2FtcGFpZ24iOm51bGwsImN1cnJlbmN5Q29kZSI6IkFSUyIsImN1cnJlbmN5U3ltYm9sIjoiJCIsImNvdW50cnlDb2RlIjoiQVJHIiwiY3VsdHVyZUluZm8iOiJlcy1BUiIsImFkbWluX2N1bHR1cmVJbmZvIjoiZXMtQVIiLCJjaGFubmVsUHJpdmFjeSI6InB1YmxpYyJ9"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Cookie": f"vtex_segment={COOKIE_SEGMENT}"
}

# -------------------
# 🔹 Diccionario de productos (Nombre: productId)
# -------------------
productos = {
    "Galletitas dulces Anillitos Terrabusi 170 g.": "680264",
    "Galletitas dulces Anillitos Terrabusi 300 g.": "694961",
    "Galletitas dulces Boca de Dama Terrabusi 170 g.": "680263",
    "Tostadas de arroz Cerealitas 160 g.": "417620",
    "Galletitas dulces Duquesa Terrabusi 115 g.": "521124",
    "Galletitas dulces Duquesa Terrabusi 354 grs": "743099",
    "Galletitas dulce Melba rellenas 360 g.": "281790",
    "Galletitas dulces Melba rellenas con crema 120 g.": "553640",
    "Galletitas de chocolate Milka rellena de mousse de chocolate 124 grs": "759453",
    "Galletitas Oreo Mini rellenas con crema sabor original 50 g.": "720547",
    "Galletitas Oreo Golden sabor vainilla rellenas con crema 354 g.": "680265",
    "Galletitas Oreo Golden sabor vainilla rellenas con crema 118 g.": "679211",
    "Galletitas Oreo rellenas con crema sabor original 182,5 g.": "715950",
    "Galletitas dulces Oreo rellenas con crema 118 g.": "715949",
    "Oreo rellenas con crema de frutilla 118 grs": "747087",
    "Galletitas Oreo Rellenas con crema sabor original 354 g.": "715951",
    "Galletitas dulces Oreo sabor maní edición limitada 118 grs": "759454",
    "Galletitas Pepitos con chips de chocolate 119 g.": "715953",
    "Galletitas dulces Variedad Terrabusi 144 g.": "715959",
    "Galletitas dulces Scons Terrabusi 160 g.": "682549",
    "Galletitas dulces Terrabusi vainilla 120 grs": "743100",
    "Galletitas dulces Terrabusi miel 120 grs": "743101",
    "Galletitas Mini Pepitos con chips de chocolate 50 g.": "720553",
    "Galletitas Pepitos con chips de chocolate 357 g. Pack x3 de 119 g.": "715954",
    "Gelletitas clásicas Lincoln vainilla 153 g.": "740136",
    "Galletitas dulces Lincoln clásicas Terrabusi tripack 459 g.": "715956",
    "Galletitas dulces Lincoln chocolate Terrabusi 153 g.": "520829",
    "Galletitas dulces Lincoln coco Terrabusi 153 g.": "521106",
    "Galletitas dulces Variedad Terrabusi mix tamaño familiar 590 g.": "715957",
    "Galletas de arroz Cerealitas 160 g.": "722432",
    "Galletitas de chocolate relleno de choco Oreo 118 g.": "747086",
    "Galletitas Oreo rellenas con crema de chocolate 118 g.": "720549",
    "Galletitas dulces Variedad Terrabusi mix chocolate tamaño familiar 300 g.": "715958",
    "Galletitas dulces Variedad Terrabusi mix vainilla tamaño familiar 300 g.": "714818",
    "Galletitas dulces Lincoln clásicas Terrabusi 219 g.": "720550",
    "Galletitas Manon 182 g.": "720548",
    "Galletitas dulces Variedad Terrabusi mix 170 g.": "714817",
    "Galletitas dulces Variedad Terrabusi mix tamaño familiar 390 g.": "714816",
    "Galletitas Oreo sin gluten 95 g.": "740135",
    "Galletitas Mini Oreo rellenas con crema sabor original 150 g.": "740134",
    "Galletitas Cerealitas avena cacao 170 g.": "747084",
    "Galletitas Cerealitas granola 170 g.": "747085",
    "Galletitas de salvado Cerealitas 624 g.": "720566",
    "Galletitas de salvado Cerealitas 208 g.": "720565",
    "Galletitas crackers Cerealitas clásicas 636 g.": "720564",
    "Galletitas crackers Cerealitas clásicas 212 g.": "720563",
    "Gomitas blueberry Bubbaloo 82,5 grs": "752372",
    "Gomitas de frutilla ácidas Bobbaloo 82,2 grs": "752373",
    "Gomitas de frutilla Bubbaloo 15 grs": "752374",
    "Gomitas mix frutal ácidas Bubbaloo 16,5 grs": "752375",
    "Gomitas de frutilla ácidas Bubbaloo 16,5 grs": "752376",
    "Caramelos Clight naranja 20 g.": "542913",
    "Caramelos Clight frambuesa 20 g.": "556096",
    "Caramelo Halls extra strong 28 grs": "722325",
    "Caramelo Halls sandia 28 g.": "723070",
    "Caramelo Halls menthol 28 g.": "723069",
    "Caramelos Halls sandia 25.2 grs": "756130",
    "Caramelos Halls cherry 25.2 grs": "756131",
    "Caramelos Halls menta lyptus 25.2 grs": "756132",
    "Caramelos Halls menthol 25.2 grs": "756133",
    "Caramelos Halls Stani miel y menta 28 g.": "571019",
    "Caramelos Halls vitamina C frutilla 28 g.": "571017",
    "Caramelo Halls cherry 28 g.": "723071",
    "Caramelos Free Halls de menta 20 grs": "750132",
    "Caramelo duro Halls cherry free 20 g.": "722326",
    "Alfajor Terrabusi chocolate clásico 50 g.": "205469",
    "Alfajor Terrabusi blanco glaseado 38 g.": "530359",
    "Alfajor Milka simple mousse 42 g.": "589445",
    "SHOT con pasta de maní 44 grs": "760861",
    "Alfajor Terrabusi triple clásico 70 g.": "353214",
    "Alfajor Terrabusi triple torta 70 g.": "666541",
    "Alfajor Milka triple mousse 55 g.": "569705",
    "Alfajor triple Milka dulce de leche 70 g.": "667749",
    "Alfajor triple Milka mousse blanco 55 g.": "481894",
    "Alfajor SHOT con maní Triple 60 g.": "353207",
    "Alfajor Pepitos triple 57 g.": "569707",
    "Alfajor triple Milka Oreo 61 g.": "667747",
    "Alfajor Oreo triple 56 g.": "680445",
    "Alfajor Tita 36 grs": "318002",
    "Chocolate Cadbury tres sueños 25 g.": "680443",
    "Chocolate Cadbury intense 25 g.": "680444",
    "Chocolate Cadbury relleno yoghurt frutilla 29 g.": "680441",
    "Chocolate Cadbury frutilla relleno yoghurt 82 g.": "680432",
    "Chocolate Cadbury tres sueños 82 g.": "680436",
    "Chocolate con almendras Cadbury 82 g.": "680434",
    "Chocolate Cadbury intense 162 g.": "680433",
    "Chocolate Cadbury relleno yoghurt frutilla 162 g.": "680435",
    "Bombón de chocolate Milka Oreo 19 g.": "674634",
    "Oblea mini Rhodesia clásicas 60 g.": "450943",
    "Oblea Rhodesia clásica 22 g.": "205427",
    "Oblea Rhodesia chocolate 22 g.": "656382",
    "Chocolate Milka chocopause 45 g.": "687564",
    "Chocolate Milka Oreo chocopause 45 g.": "687565",
    "Habanitos Terrabusi de chocolate 60 grs": "450942",
    "Obleas Snacky mini chocolate 60 g.": "450938",
    "Chocolate Milka bis oblea 105,6 g.": "629728",
    "Chocolate Milka Oreo bis oblea 105,6 g.": "650253",
    "Oblea Tita chocolate 19 g.": "680422",
    "Chocolate Toblerone 100 g.": "294724",
    "Chocolate Milka Oreo Lila Go 37 g.": "634022",
    "Chocolate Milka con leche 20 g.": "629262",
    "Chocolate Milka relleno dulce de leche 67,5 g.": "566560",
    "Chocolate Milka blanco relleno dulce de leche 67,5 g.": "566564",
    "Chocolate Milka relleno dulce de leche 135 g.": "571956",
    "Chocolate Milka blanco 55 g.": "628576",
    "Chocolate Milka con leche 55 g.": "628578",
    "Chocolate Milka con leche 150 g.": "601881",
    "Tableta chocolate choco swing Milka 300 g.": "429164",
    "Chocolate Milka con almendras 55 g.": "628579",
    "Chocolate Milka con almendras 155 g.": "601887",
    "Chocolate Milka con castañas 55 g.": "628580",
    "Chocolate Milka con castañas 155 g.": "601884",
    "Chocolate Milka Oreo blanco 20 g.": "629259",
    "Chocolate Milka Oreo blanco 55 g.": "628575",
    "Chocolate  Milka Oreo 100 g.": "585325",
    "Chocolate Milka Oreo blanco 155 g.": "601890",
    "Chocolate Milka Oreo 300 g.": "600631",
    "Tableta de chocolate Milka whole nuts 95 grs": "759141",
    "Chocolate Milka aireado con leche 50 g.": "680438",
    "Chocolate Milka aireado combinado 50 g.": "680442",
    "Chocolate Milka aireado con almendras 50 g.": "680439",
    "Chocolate Milka aireado con leche 110 g.": "680427",
    "Chocolate Milka aireado combinado 110 g.": "680428",
    "Chocolate Milka aireado con almendras 110 g.": "680429",
    "Tableta de chocolate Milka strawb cheesecake 300 g.": "737288",
    "Chocolate Milka Oreo Brownie 100 grs": "737289",
    "Tableta de chocolate Milka almond caramel 300 grs": "759143",
    "Tableta de chocolate Milka con dulce de leche 29 grs": "762887",
    "Tableta de chocolate blanco Milka con dulce de leche 29 grs": "762888",
    "Tableta de chocolate aireado leche Milka 25 grs": "762889",
    "Tableta de chocolate aireado combinado Milka 25 grs": "762890",
    "Chocolate SHOT con maní 35 g.": "532502",
    "Chocolate SHOT con maní 170 g.": "582637",
    "Chocolate SHOT con maní 90 g.": "550217",
    "Chocolate SHOT blanco con maní 35 g.": "722327",
    "Gelatina en polvo light Royal frutos rojos 25 g.": "586115",
    "Gelatina sin sabor Royal 14 g.": "662143",
    "Polvo para hornear Royal en sobre 50 g.": "687631",
    "Polvo para Hornear Royal 100 g.": "617373",
    "Torta para preparar Royal sabor vainilla 500 g.": "717825",
    "Torta para preparar Royal sabor chocolate 500 g.": "717826",
    "Mousse chocolate manjares light Royal 40 g.": "602705",
    "Postre en polvo Royal chocolate 65 g.": "608097",
    "Gelatina Royal sabor frutilla 25 g.": "714815",
    "Gelatina Royal sabor frambuesa 25 g.": "714809",
    "Gelatina Royal cereza 25 g.": "714810",
    "Gelatina Royal sabor durazno 25 g.": "714813",
    "Gelatina Royal sabor naranja 22 g.": "714812",
    "Gelatina Royal sabor cereza 25 g.": "714811",
    "Gelatina Royal sabor frutos rojos 25 g.": "714814",
    "Flan Royal de vainilla 60 g.": "716930",
    "Mousse Royal de chocolate 65 g.": "716932",
    "Mousse de chocolate Royal light 40 g.": "716927",
    "Postre Royal de vainilla 75 g.": "716922",
    "Postre de chocolate Royal en sobre 65 g.": "716928",
    "Postre Royal de frutilla 75 g.": "716923",
    "Postre en polvo Royal dulce de leche 75 g.": "602697",
    "Postre Royal de vainilla 43 g.": "716925",
    "Postre Royal de chocolate 50 g.": "716926",
    "Crema chantilly Royal 50 g.": "716931",
    "Chicles Beldent mandarina 20 g.": "697158",
    "Chicles Beldent sandia 20 g.": "736393",
    "Chicle globo Beldent de frutila 20 grs": "756135",
    "Chicles Beldent menta 20 g.": "670221",
    "Chicles Beldent menta fuerte 20 g.": "670219",
    "Chicles Beldent mentol 20 g.": "670216",
    "Chicles Beldent globo 20 g.": "670218",
    "Chicles Beldent frutilla 20 g.": "670215",
    "Chicles Beldent Infinit menta 13,3 g.": "680269",
    "Chicles Beldent Infinit mentol 13,3 g.": "680270",
    "Chicles Beldent Infinit citrus 13,3 g.": "680271",
    "Chicles Beldent Infinit blueberry 13,3 g.": "680272",
    "Chicles Beldent Infinit menta 26,6 g.": "680347",
    "Chicles Beldent Infinit mentol 26,6 g.": "680348",
    "Chicles Beldent Infinit citrus 26,6 g.": "680349",
    "Chicles Beldent Infinit Blueberry 26,6 g.": "680350",
    "Chicle de menta Bubbaloo 5 g.": "736394",
    "Chicle de tutti frutti Bubbaloo 5 g.": "736395",
    "Chicle de frutilla Bubbaloo 5 g.": "736396",
    "Chicle de uva Bubbaloo 5 g.": "736397",
    "Jugo en polvo Clight limonada rosa 8 g.": "693718",
    "Jugo en polvo Clight ananá 7g.": "711433",
    "Jugo en polvo Clight limonada 8 g.": "711434",
    "Jugo en polvo Clight naranja mango 7g.": "711778",
    "Jugo en polvo Clight naranja durazno 7.5 g.": "711435",
    "Jugo en polvo Clight manzana verde 7.5 g.": "711436",
    "Jugo en polvo Clight manzana deliciosa 7 g.": "711437",
    "Jugo en polvo Clight limonada maracuyá 7,5 g.": "726610",
    "Jugo en polvo Clight naranja 8 g.": "711438",
    "Jugo en polvo Clight naranja dulce 7.5 g.": "711439",
    "Jugo en polvo Clight pomelo rosado 8 g.": "711440",
    "Jugo en polvo Clight pera 7 g.": "711441",
    "Jugo en polvo Clight pomelo amarillo 8 g.": "711442",
    "Jugo en polvo Clight mandarina 8 g.": "711443",
    "Jugo en polvo Clight naranja stevia 9.5 g.": "711444",
    "Jugo en polvo Clight limonada stevia 7.5 g.": "718995",
    "Jugo en polvo Clight manzana stevia 7.5 g.": "711445",
    "Jugo en polvo Clight limonada arándanos 7,5 grs": "745774",
    "Jugo en polvo Tang frutilla 15 g.": "711448",
    "Jugo en polvo Tang naranja 15 g.": "711449",
    "Jugo en polvo Tang manzana 15 g.": "711450",
    "Jugo en polvo Tang naranja dulce 15 g.": "711451",
    "Jugo en polvo Tang naranja mango 15 g.": "711781",
    "Jugo en polvo Tang limonada dulce 15 g.": "711782",
    "Jugo en polvo Tang multifruta 15 g.": "711783",
    "Jugo en polvo Tang pomelo rosado 15 g.": "711784",
    "Jugo en polvo Tang naranja banana 15 g.": "711785",
    "Jugo en polvo Tang naranja durazno en sobre 15 g.": "718997",
    "Jugo en polvo Tang sabor pera 15 g.": "711786",
    "Jugo en polvo Tang durazno 15 g.": "711787",
    "Jugo en polvo Tang naranja lima 15 g.": "711452",
    "Jugo en polvo Tang mix naranja frutilla maracuyá 15 g.": "711453",
    "Jugo en polvo Tang uva 15 g.": "711454",
    "Jugo en polvo Tang ananá 15 g.": "711788",
    "Jugo en polvo Tang mandarina 15 grs": "749990",
    "Jugo en polvo Verao naranja 7 g. Rinde 1 L.": "711446",
    "Jugo en polvo Verao manzana 7 g. Rinde 1 L": "711447",
    "Jugo en polvo Verao naranja durazno 7 g.": "711779",
    "Jugo en polvo Verao ananá 7 g.": "711780",
}

# -------------------
# 🔹 Streamlit UI
# -------------------
st.title("📊 Precios Carrefour - API (Sucursal Hiper Olivos)")
st.write("Obtiene los precios de los productos listados directamente desde la API de Carrefour, aplicando la cookie de **Hiper Olivos**.")

if st.button("🔍 Ejecutar scraping"):
    with st.spinner("⏳ Procesando... Esto puede tardar unos segundos"):
        resultados = []

        for nombre, product_id in productos.items():
            try:
                url = f"https://www.carrefour.com.ar/api/catalog_system/pub/products/search?fq=productId:{product_id}"
                r = requests.get(url, headers=HEADERS, timeout=10)
                data = r.json()

                if not data:
                    resultados.append({"productId": product_id, "Nombre": nombre, "Precio": "❌ Sin datos"})
                    continue

                offer = data[0]['items'][0]['sellers'][0]['commertialOffer']
                price_list = offer.get('ListPrice', 0)
                price = offer.get('Price', 0)

                # Preferimos precio de lista si existe, sino precio actual
                final_price = price_list if price_list > 0 else price

                if final_price > 0:
                    precio_formateado = f"{final_price:,.2f}".replace(",", "X").replace(".", ",").replace("X", "")
                    resultados.append({"productId": product_id, "Nombre": nombre, "Precio": precio_formateado})
                else:
                    resultados.append({"productId": product_id, "Nombre": nombre, "Precio": "no hay stock"})

            except Exception:
                resultados.append({"productId": product_id, "Nombre": nombre, "Precio": "⚠️ Error"})

        # --- Crear DataFrame y mostrarlo
        df = pd.DataFrame(resultados, columns=["productId", "Nombre", "Precio"])
        st.success("✅ Scraping completado vía API")
        st.dataframe(df)

        # --- Botón de descarga CSV
        fecha = datetime.now().strftime("%Y-%m-%d")
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇ Descargar CSV",
            data=csv,
            file_name=f"precios_hiper_olivos_{fecha}.csv",
            mime="text/csv",
        )
