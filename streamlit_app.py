# basic imports
import asyncio
import streamlit as st
import pandas as pd
import re
from datetime import date, timedelta

# imports for search console libraries
import searchconsole
from apiclient import discovery
from google_auth_oauthlib.flow import Flow

# imports for aggrid
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid.shared import JsCode
from st_aggrid import GridUpdateMode, DataReturnMode

# all other imports
import os
from streamlit_elements import Elements

###############################################################################

# The code below is for the layout of the page
if "widen" not in st.session_state:
    layout = "centered"
else:
    layout = "wide" if st.session_state.widen else "centered"

st.set_page_config(
    layout=layout, page_title="Google Search Console Connector", page_icon="🔌"
)

###############################################################################

# row limit
RowCap = 100000


###############################################################################

tab1, tab2 = st.tabs(["Extractor", "Comparativa períodos"])

with tab1:

    st.sidebar.image("logo.png", width=290)

    st.sidebar.markdown("")

    st.write("")

    # Convert secrets from the TOML file to strings
    clientSecret = "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"
    clientId = "191921890644-cs9g4o8prro05lc89m6t3k3drtu04kuf.apps.googleusercontent.com"
    redirectUri = "https://app-search-console-extractor.streamlit.app"

    st.markdown("")

    if "my_token_input" not in st.session_state:
        st.session_state["my_token_input"] = ""

    if "my_token_received" not in st.session_state:
        st.session_state["my_token_received"] = False

    def charly_form_callback():
        # st.write(st.session_state.my_token_input)
        st.session_state.my_token_received = True
        code = st.experimental_get_query_params()["code"][0]
        st.session_state.my_token_input = code

    with st.sidebar.form(key="my_form"):

        st.markdown("")

        mt = Elements()

        mt.button(
            "Logueate con tu cuenta de Google",
            target="_blank",
            size="large",
            variant="contained",
            start_icon=mt.icons.exit_to_app,
            onclick="none",
            style={"color": "#FFFFFF", "background": "#FF4B4B"},
            href="https://accounts.google.com/o/oauth2/auth?response_type=code&client_id="
            + clientId
            + "&redirect_uri="
            + redirectUri
            + "&scope=https://www.googleapis.com/auth/webmasters.readonly&access_type=offline&prompt=consent",
        )

        mt.show(key="687")

        credentials = {
            "installed": {
                "client_id": clientId,
                "client_secret": clientSecret,
                "redirect_uris": [],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://accounts.google.com/o/oauth2/token",
            }
        }

        flow = Flow.from_client_config(
            credentials,
            scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
            redirect_uri=redirectUri,
        )

        auth_url, _ = flow.authorization_url(prompt="consent")

        submit_button = st.form_submit_button(
            label="Conectar GSC API", on_click=charly_form_callback
        )

        st.write("")


        with st.expander("Comprobar Oauth token"):
            code = st.text_input(
                "",
                key="my_token_input",
                label_visibility="collapsed",
            )

        st.write("")

    container3 = st.sidebar.container()

    st.sidebar.write("")

    try:

        if st.session_state.my_token_received == False:

            with st.form(key="my_form2"):

                # text_input_container = st.empty()
                webpropertiesNEW = st.text_input(
                    "Seleccionar propiedad web (autentificate primero en el panel izquierdo)",
                    value="",
                    disabled=True,
                )

                filename = webpropertiesNEW.replace("https://www.", "")
                filename = filename.replace("http://www.", "")
                filename = filename.replace(".", "")
                filename = filename.replace("/", "")

                col1, col2, col3 = st.columns(3)

                with col1:
                    dimension = st.selectbox(
                        "Dimension 1",
                        (
                            "query",
                            "page",
                            "date",
                            "device",
                            "searchAppearance",
                            "country",
                        ),
                        help="Choose a top dimension",
                    )

                with col2:
                    nested_dimension = st.selectbox(
                        "Dimension 2",
                        (
                            "none",
                            "query",
                            "page",
                            "date",
                            "device",
                            "searchAppearance",
                            "country",
                        ),
                        help="Choose a nested dimension",
                    )

                with col3:
                    nested_dimension_2 = st.selectbox(
                        "Dimension 3",
                        (
                            "none",
                            "query",
                            "page",
                            "date",
                            "device",
                            "searchAppearance",
                            "country",
                        ),
                        help="Choose a second nested dimension",
                    )

                st.write("")

                col1, col2 = st.columns(2)

                with col1:
                    search_type = st.selectbox(
                        "Search type",
                        ("web", "video", "image", "news", "googleNews"),
                        help="""
                        Specify the search type you want to retrieve
                        -   **Web**: Results that appear in the All tab. This includes any image or video results shown in the All results tab.
                        -   **Image**: Results that appear in the Images search results tab.
                        -   **Video**: Results that appear in the Videos search results tab.
                        -   **News**: Results that show in the News search results tab.

                        """,
                    )

                with col2:
                    # Obtener la fecha de hoy
                    today = date.today()
                    # Calcular la fecha de hace 16 meses
                    sixteen_months_ago = today - timedelta(days=486)
                    # Widget para seleccionar la fecha de inicio
                    start_date = st.date_input(
                        "Fecha de inicio",
                        value=sixteen_months_ago,  # Valor por defecto: 16 meses atrás
                        min_value=sixteen_months_ago,  # Fecha mínima: 16 meses atrás
                        max_value=today,  # Fecha máxima: hoy
                        help="Selecciona la fecha de inicio del período"
                    )
                    # Widget para seleccionar la fecha de fin
                    end_date = st.date_input(
                        "Fecha de fin",
                        value=today,  # Valor por defecto: hoy
                        min_value=start_date,  # Fecha mínima: la fecha de inicio
                        max_value=today,  # Fecha máxima: hoy
                        help="Selecciona la fecha de fin del período"
                    )
                    # timescale = st.selectbox(
                    #     "Date range",
                    #     (
                    #         "Last 7 days",
                    #         "Last 30 days",
                    #         "Last 3 months",
                    #         "Last 6 months",
                    #         "Last 12 months",
                    #         "Last 16 months",
                    #     ),
                    #     index=0,
                    #     help="Specify the date range",
                    # )

                    # if timescale == "Last 7 days":
                    #     timescale = -7
                    # elif timescale == "Last 30 days":
                    #     timescale = -30
                    # elif timescale == "Last 3 months":
                    #     timescale = -91
                    # elif timescale == "Last 6 months":
                    #     timescale = -182
                    # elif timescale == "Last 12 months":
                    #     timescale = -365
                    # elif timescale == "Last 16 months":
                    #     timescale = -486

                st.write("")

                with st.expander("✨ Filtros avanzados", expanded=False):

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        filter_page_or_query = st.selectbox(
                            "Dimension para filtrar #1",
                            ("query", "page", "device", "searchAppearance", "country"),
                            help="""
                            Puedes elegir una dimension para filtrar.
                            """,
                        )

                    with col2:
                        filter_type = st.selectbox(
                            "Filter type",
                            (
                                "contains",
                                "equals",
                                "notContains",
                                "notEquals",
                                "includingRegex",
                                "excludingRegex",
                            ),
                            help="""
                            Note that if you use Regex in your filter, you must follow the `RE2` syntax.
                            """,
                        )

                    with col3:
                        filter_keyword = st.text_input(
                            "Keyword(s) to filter ",
                            "",
                            help="Add the keyword(s) you want to filter",
                        )

                    with col1:
                        filter_page_or_query2 = st.selectbox(
                            "Dimension para filtrar #2",
                            ("query", "page", "device", "searchAppearance", "country"),
                            key="filter_page_or_query2",
                            help="""
                            Puedes elegir una segunda dimension para filtrar.
                            """,
                        )

                    with col2:
                        filter_type2 = st.selectbox(
                            "Filter type",
                            (
                                "contains",
                                "equals",
                                "notContains",
                                "notEquals",
                                "includingRegex",
                                "excludingRegex",
                            ),
                            key="filter_type2",
                            help="""
                            Note that if you use Regex in your filter, you must follow the `RE2` syntax.
                            """,
                        )

                    with col3:
                        filter_keyword2 = st.text_input(
                            "Keyword(s) to filter ",
                            "",
                            key="filter_keyword2",
                            help="Add the keyword(s) you want to filter",
                        )

                    with col1:
                        filter_page_or_query3 = st.selectbox(
                            "Dimension para filtrar #3",
                            ("query", "page", "device", "searchAppearance", "country"),
                            key="filter_page_or_query3",
                            help="""
                            Puedes elegir una tercera dimension para filtrar.
                            """,
                        )

                    with col2:
                        filter_type3 = st.selectbox(
                            "Filter type",
                            (
                                "contains",
                                "equals",
                                "notContains",
                                "notEquals",
                                "includingRegex",
                                "excludingRegex",
                            ),
                            key="filter_type3",
                            help="""
                            Note that if you use Regex in your filter, you must follow the `RE2` syntax.
                            """,
                        )

                    with col3:
                        filter_keyword3 = st.text_input(
                            "Keyword(s) to filter ",
                            "",
                            key="filter_keyword3",
                            help="Add the keyword(s) you want to filter",
                        )

                    st.write("")

                submit_button = st.form_submit_button(
                    label="Extracción de datos", on_click=charly_form_callback
                )

            if (nested_dimension != "none") and (nested_dimension_2 != "none"):

                if (
                    (dimension == nested_dimension)
                    or (dimension == nested_dimension_2)
                    or (nested_dimension == nested_dimension_2)
                ):
                    st.warning(
                        "🚨 La dimensiones primeras y secundarias no pueden ser iguales, por favor, asegúrate de usar dimensiones únicas."
                    )
                    st.stop()

                else:
                    pass

            elif (nested_dimension != "none") and (nested_dimension_2 == "none"):
                if dimension == nested_dimension:
                    st.warning(
                        "🚨 Dimension and nested dimensions cannot be the same, please make sure you choose unique dimensions."
                    )
                    st.stop()
                else:
                    pass

            else:
                pass

        if st.session_state.my_token_received == True:

            @st.cache_resource
            def get_account_site_list_and_webproperty(token):
                flow.fetch_token(code=token)
                credentials = flow.credentials
                service = discovery.build(
                    serviceName="webmasters",
                    version="v3",
                    credentials=credentials,
                    cache_discovery=False,
                )

                account = searchconsole.account.Account(service, credentials)
                site_list = service.sites().list().execute()
                return account, site_list

            account, site_list = get_account_site_list_and_webproperty(
                st.session_state.my_token_input
            )

            first_value = list(site_list.values())[0]

            lst = []
            for dicts in first_value:
                a = dicts.get("siteUrl")
                lst.append(a)

            if lst:

                container3.info("✔️ GSC credentials OK!")

                with st.form(key="my_form2"):

                    webpropertiesNEW = st.selectbox("Seleccionar propiedad web", lst)

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        dimension = st.selectbox(
                            "Dimension 1",
                            (
                                "query",
                                "page",
                                "date",
                                "device",
                                "searchAppearance",
                                "country",
                            ),
                            help="Choose your top dimension",
                        )

                    with col2:
                        nested_dimension = st.selectbox(
                            "Dimension 2",
                            (
                                "none",
                                "query",
                                "page",
                                "date",
                                "device",
                                "searchAppearance",
                                "country",
                            ),
                            help="Choose a nested dimension",
                        )

                    with col3:
                        nested_dimension_2 = st.selectbox(
                            "Dimension 3",
                            (
                                "none",
                                "query",
                                "page",
                                "date",
                                "device",
                                "searchAppearance",
                                "country",
                            ),
                            help="Choose a second nested dimension",
                        )

                    st.write("")

                    col1, col2 = st.columns(2)

                    with col1:
                        search_type = st.selectbox(
                            "Search type",
                            ("web", "news", "video", "googleNews", "image"),
                            help="""
                        Specify the search type you want to retrieve
                        -   **Web**: Results that appear in the All tab. This includes any image or video results shown in the All results tab.
                        -   **Image**: Results that appear in the Images search results tab.
                        -   **Video**: Results that appear in the Videos search results tab.
                        -   **News**: Results that show in the News search results tab.

                        """,
                        )

                    with col2:
                        # Obtener la fecha de hoy
                        today = date.today()
                        # Calcular la fecha de hace 16 meses
                        sixteen_months_ago = today - timedelta(days=486)
                        # Widget para seleccionar la fecha de inicio
                        start_date = st.date_input(
                            "Fecha de inicio",
                            value=sixteen_months_ago,  # Valor por defecto: 16 meses atrás
                            min_value=sixteen_months_ago,  # Fecha mínima: 16 meses atrás
                            max_value=today,  # Fecha máxima: hoy
                            help="Selecciona la fecha de inicio del período"
                        )
                        # Widget para seleccionar la fecha de fin
                        end_date = st.date_input(
                            "Fecha de fin",
                            value=today,  # Valor por defecto: hoy
                            min_value=start_date,  # Fecha mínima: la fecha de inicio
                            max_value=today,  # Fecha máxima: hoy
                            help="Selecciona la fecha de fin del período"
                        )
                        # timescale = st.selectbox(
                        #     "Date range",
                        #     (
                        #         "Last 7 days",
                        #         "Last 30 days",
                        #         "Last 3 months",
                        #         "Last 6 months",
                        #         "Last 12 months",
                        #         "Last 16 months",
                        #     ),
                        #     index=0,
                        #     help="Specify the date range",
                        # )

                        # if timescale == "Last 7 days":
                        #     timescale = -7
                        # elif timescale == "Last 30 days":
                        #     timescale = -30
                        # elif timescale == "Last 3 months":
                        #     timescale = -91
                        # elif timescale == "Last 6 months":
                        #     timescale = -182
                        # elif timescale == "Last 12 months":
                        #     timescale = -365
                        # elif timescale == "Last 16 months":
                        #     timescale = -486

                    st.write("")

                    with st.expander("✨ Advanced Filters", expanded=False):

                        col1, col2, col3 = st.columns(3)

                        with col1:
                            filter_page_or_query = st.selectbox(
                                "Dimension to filter #1",
                                (
                                    "query",
                                    "page",
                                    "device",
                                    "searchAppearance",
                                    "country",
                                ),
                                help="You can choose to filter dimensions and apply filters before executing a query.",
                            )

                        with col2:
                            filter_type = st.selectbox(
                                "Filter type",
                                (
                                    "contains",
                                    "equals",
                                    "notContains",
                                    "notEquals",
                                    "includingRegex",
                                    "excludingRegex",
                                ),
                                help="Note that if you use Regex in your filter, you must follow `RE2` syntax.",
                            )

                        with col3:
                            filter_keyword = st.text_input(
                                "Keyword(s) to filter ",
                                "",
                                help="Add the keyword(s) you want to filter",
                            )

                        with col1:
                            filter_page_or_query2 = st.selectbox(
                                "Dimension to filter #2",
                                (
                                    "query",
                                    "page",
                                    "device",
                                    "searchAppearance",
                                    "country",
                                ),
                                key="filter_page_or_query2",
                                help="You can choose to filter dimensions and apply filters before executing a query.",
                            )

                        with col2:
                            filter_type2 = st.selectbox(
                                "Filter type",
                                (
                                    "contains",
                                    "equals",
                                    "notContains",
                                    "notEquals",
                                    "includingRegex",
                                    "excludingRegex",
                                ),
                                key="filter_type2",
                                help="Note that if you use Regex in your filter, you must follow `RE2` syntax.",
                            )

                        with col3:
                            filter_keyword2 = st.text_input(
                                "Keyword(s) to filter ",
                                "",
                                key="filter_keyword2",
                                help="Add the keyword(s) you want to filter",
                            )

                        with col1:
                            filter_page_or_query3 = st.selectbox(
                                "Dimension to filter #3",
                                (
                                    "query",
                                    "page",
                                    "device",
                                    "searchAppearance",
                                    "country",
                                ),
                                key="filter_page_or_query3",
                                help="You can choose to filter dimensions and apply filters before executing a query.",
                            )

                        with col2:
                            filter_type3 = st.selectbox(
                                "Filter type",
                                (
                                    "contains",
                                    "equals",
                                    "notContains",
                                    "notEquals",
                                    "includingRegex",
                                    "excludingRegex",
                                ),
                                key="filter_type3",
                                help="Note that if you use Regex in your filter, you must follow `RE2` syntax.",
                            )

                        with col3:
                            filter_keyword3 = st.text_input(
                                "Keyword(s) to filter ",
                                "",
                                key="filter_keyword3",
                                help="Add the keyword(s) you want to filter",
                            )

                        st.write("")

                    submit_button = st.form_submit_button(
                        label="Fetch GSC API data", on_click=charly_form_callback
                    )

                if (nested_dimension != "none") and (nested_dimension_2 != "none"):

                    if (
                        (dimension == nested_dimension)
                        or (dimension == nested_dimension_2)
                        or (nested_dimension == nested_dimension_2)
                    ):
                        st.warning(
                            "🚨 Dimension and nested dimensions cannot be the same, please make sure you choose unique dimensions."
                        )
                        st.stop()

                    else:
                        pass

                elif (nested_dimension != "none") and (nested_dimension_2 == "none"):
                    if dimension == nested_dimension:
                        st.warning(
                            "🚨 Dimension and nested dimensions cannot be the same, please make sure you choose unique dimensions."
                        )
                        st.stop()
                    else:
                        pass

                else:
                    pass
        if submit_button:
            def get_search_console_data(webproperty):
                if webproperty is not None:
                    report = (
                        webproperty.query.search_type(search_type)
                        .range(start_date, end_date)
                        .dimension(dimension)
                        .filter(filter_page_or_query, filter_keyword, filter_type)
                        .filter(filter_page_or_query2, filter_keyword2, filter_type2)
                        .filter(filter_page_or_query3, filter_keyword3, filter_type3)
                        .limit(RowCap)
                        .get()
                        .to_dataframe()
                    )
                    return report
                else:
                    st.warning("No webproperty found")
                    st.stop()

            def get_search_console_data_nested(webproperty):
                if webproperty is not None:
                    # query = webproperty.query.range(start="today", days=days).dimension("query")
                    report = (
                        webproperty.query.search_type(search_type)
                        .range(start_date, end_date)
                        .dimension(dimension, nested_dimension)
                        .filter(filter_page_or_query, filter_keyword, filter_type)
                        .filter(filter_page_or_query2, filter_keyword2, filter_type2)
                        .filter(filter_page_or_query3, filter_keyword3, filter_type3)
                        .limit(RowCap)
                        .get()
                        .to_dataframe()
                    )
                    return report

            def get_search_console_data_nested_2(webproperty):
                if webproperty is not None:
                    # query = webproperty.query.range(start="today", days=days).dimension("query")
                    report = (
                        webproperty.query.search_type(search_type)
                        .range(start_date, end_date)
                        .dimension(dimension, nested_dimension, nested_dimension_2)
                        .filter(filter_page_or_query, filter_keyword, filter_type)
                        .filter(filter_page_or_query2, filter_keyword2, filter_type2)
                        .filter(filter_page_or_query3, filter_keyword3, filter_type3)
                        .limit(RowCap)
                        .get()
                        .to_dataframe()
                    )
                    return report

            # Here are some conditions to check which function to call

            if nested_dimension == "none" and nested_dimension_2 == "none":

                webproperty = account[webpropertiesNEW]

                df = get_search_console_data(webproperty)

                if df.empty:
                    st.warning(
                        "🚨 There's no data for your selection, please refine your search with different criteria"
                    )
                    st.stop()

            elif nested_dimension_2 == "none":

                webproperty = account[webpropertiesNEW]

                df = get_search_console_data_nested(webproperty)

                if df.empty:
                    st.warning(
                        "🚨 DataFrame is empty! Please refine your search with different criteria"
                    )
                    st.stop()

            else:

                webproperty = account[webpropertiesNEW]

                df = get_search_console_data_nested_2(webproperty)

                if df.empty:
                    st.warning(
                        "🚨 DataFrame is empty! Please refine your search with different criteria"
                    )
                    st.stop()

            st.write("")

            st.write(
                "##### Nº de resultados devueltos por API: ",
                len(df.index),
            )

            col1, col2, col3 = st.columns([1, 1, 1])

            with col1:
                st.caption("")
                check_box = st.checkbox(
                    "Ag-Grid mode", help="Tick this box to see your data in Ag-grid!"
                )
                st.caption("")

            with col2:
                st.caption("")
                st.checkbox(
                    "Widen layout",
                    key="widen",
                    help="Tick this box to switch the layout to 'wide' mode",
                )
                st.caption("")

            if not check_box:

                @st.cache
                def convert_df(df):
                    return df.to_csv().encode("utf-8")

                csv = convert_df(df)

                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="large_df.csv",
                    mime="text/csv",
                )

                st.caption("")

                st.dataframe(df, height=500)

            elif check_box:

                df = df.reset_index()

                gb = GridOptionsBuilder.from_dataframe(df)
                # enables pivoting on all columns, however i'd need to change ag grid to allow export of pivoted/grouped data, however it select/filters groups
                gb.configure_default_column(
                    enablePivot=True, enableValue=True, enableRowGroup=True
                )
                gb.configure_selection(selection_mode="multiple", use_checkbox=True)
                gb.configure_side_bar()
                gridOptions = gb.build()
                st.info(
                    f"""
                            💡 Tip! Hold the '⇧ Shift' key when selecting rows to select multiple rows at once!
                            """
                )

                response = AgGrid(
                    df,
                    gridOptions=gridOptions,
                    enable_enterprise_modules=True,
                    update_mode=GridUpdateMode.MODEL_CHANGED,
                    data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
                    height=1000,
                    fit_columns_on_grid_load=True,
                    configure_side_bar=True,
                )

    except ValueError as ve:

        st.warning("⚠️ You need to sign in to your Google account first!")

    except IndexError:
        st.info(
            "⛔ It seems you haven’t correctly configured Google Search Console! Click [here](https://support.google.com/webmasters/answer/9008080?hl=en) for more information on how to get started!"
        )


# Segunda pestaña: Comparador de períodos

with tab2:
    st.write("")
    st.write("")

    # Campos para subir los archivos CSV
    uploaded_file_pre = st.file_uploader("Sube el archivo CSV del primer periodo", type="csv")
    uploaded_file_post = st.file_uploader("Sube el archivo CSV del segundo periodo", type="csv")

    if uploaded_file_pre and uploaded_file_post:
        # Leer los datos de los archivos CSV
        df_pre = pd.read_csv(uploaded_file_pre)
        df_post = pd.read_csv(uploaded_file_post)

        try:
            # Unir los dos DataFrames, validando que no haya duplicados
            df = pd.merge(df_pre, df_post, on=["page", "query"], how="outer", suffixes=("_pre", "_post"), validate="one_to_one")
            
            # Crear la columna "Tipología"
            def obtener_tipologia(pagina):
                if re.search(r"categoria", pagina):
                    return "Categoria"
                elif re.search(r"producto", pagina):
                    return "Producto"
                else:
                    return "Otro"
            df["Tipología"] = df["page"].apply(obtener_tipologia)

            # Crear la columna "Brand/No Brand"
            def brand_no_brand(pagina):
                if re.search(r"nombre_marca", pagina):
                    return "Brand"
                else:
                    return "No Brand"
            df["Brand/No Brand"] = df["page"].apply(brand_no_brand)

            # Rellenar valores nulos con 0
            df.fillna(0, inplace=True)

            # Calcular las columnas "Dif", "Estado" y "Exclusion"
            df["Dif"] = df["position_pre"] - df["position_post"]

            def calcular_estado(row):
                if row["impressions_post"] == 0:
                    return "Perdida"
                elif row["impressions_pre"] == 0 and row["impressions_post"] > 0:
                    return "Ganada"
                elif row["Dif"] > 0:
                    return "Mejora"
                elif row["Dif"] < 0:
                    return "Empeora"
                elif -0.5 <= row["Dif"] <= 0.5:
                    return "Sin cambios"
                else:
                    return "Otro"
            df["Estado"] = df.apply(calcular_estado, axis=1)

            def calcular_exclusion(estado):
                if estado in ("Perdida", "Ganada"):
                    return "Si"
                else:
                    return "No"
            df["Exclusion"] = df["Estado"].apply(calcular_exclusion)

            # Seleccionar las columnas y el orden deseado
            df = df[["page", "Tipología", "Brand/No Brand", "query", "clicks_pre", "clicks_post", 
                     "impressions_pre", "impressions_post", "ctr_pre", "ctr_post", "position_pre", 
                     "position_post", "Dif", "Estado", "Exclusion"]]

            # Renombrar las columnas para que coincidan con la especificación
            df = df.rename(columns={
                "page": "Page",
                "query": "Query",
                "clicks_pre": "Clicks Pre",
                "clicks_post": "Clicks Post",
                "impressions_pre": "Impressions Pre",
                "impressions_post": "Impressions Post",
                "ctr_pre": "CTR Pre",
                "ctr_post": "CTR Post",
                "position_pre": "Position Pre",
                "position_post": "Position Post"
            })

            # Antes de exportar, convertir las columnas numéricas al formato deseado
            columns_to_round = ["Clicks Pre", "Clicks Post", "Impressions Pre", "Impressions Post"]
            df[columns_to_round] = df[columns_to_round].astype(int)

            # Definir el formato para las columnas decimales
            decimal_columns = ["CTR Pre", "CTR Post", "Position Pre", "Position Post", "Dif"]
            for col in decimal_columns:
                df[col] = df[col].map(lambda x: str(x).replace('.', ','))

            # Mostrar el DataFrame resultante
            st.dataframe(df)

            # Botón para descargar el DataFrame como CSV
            #csv = df.to_csv(index=False).encode('utf-8')
            csv = df.to_csv(index=False, decimal=',').encode('utf-8')
            st.download_button(
                label="Descargar CSV",
                data=csv,
                file_name='dataframe_unificado.csv',
                mime='text/csv',
            )

        except pd.errors.MergeError:
            st.error("Error: No se encontraron duplas de 'page' y 'query' en los archivos CSV. Por favor, revisa tus archivos e intenta de nuevo.")