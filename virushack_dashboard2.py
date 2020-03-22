import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import datetime
import requests
import random
from PIL import Image
from io import BytesIO
import boto3
import json
import datetime

import pydeck as pdk
import pandas as pd


st.title("Social Distancing Dashboard")

date = datetime.datetime.now()
url_topojson = 'https://raw.githubusercontent.com/AliceWi/TopoJSON-Germany/master/germany.json'




@st.cache()
def load_s3_data():
    s3_client = boto3.client("s3")

    response = s3_client.get_object(Bucket='sdd-s3-basebucket',
                                    Key='aggdata/live')

    # response = s3_client.get_object(Bucket='sdd-s3-basebucket', Key='googleplaces/{}/{}/{}/{}'.format(str(date.year).zfill(4), str(date.month).zfill(2), str(date.day).zfill(2), str(date.hour-1).zfill(2)))
    bytes_array = response["Body"].read()
    json_data = json.loads(bytes_array)

    return json_data
    # string_array = bytes_array.decode("utf-8")



# county_names, county_ids, mock_scores, gmaps_scores, hystreet_scores, cycle_scores = load_mock_data()



df_mock_scores = pd.DataFrame(load_s3_data())

standard_orte = ["Aachen","Tübingen"]

county_names = list(set(df_mock_scores["name"].values))

response = requests.get('https://github.com/socialdistancingdashboard/virushack/raw/master/logo/logo_with_medium_text.png')
img = Image.open(BytesIO(response.content))
st.sidebar.image(img, use_column_width=True)
places = st.sidebar.multiselect('Welche Orte?',list(set(county_names)), standard_orte)
# start_date = st.sidebar.date_input('Datum', datetime.date(2020,3,22))
start_date = st.sidebar.date_input('Datum', datetime.date(2020,3,22))

data_sources = st.sidebar.multiselect('Welche Daten?',['gmap_score', 'hystreet_score', "cycle_score"],"gmap_score")

#calculate average score based on selected data_sources
if len(data_sources) > 0:
    # df_mock_scores["average_score"] = df_mock_scores[data_sources].mean(axis=1)
    df_mock_scores["gmap_score"] = df_mock_scores[data_sources].mean(axis=1)
# else:
#     df_mock_scores["average_score"] = [0] * len(df_mock_scores)

#filter scores based on selected places
df_mock_scores["filtered_score"] = np.where(df_mock_scores["name"].isin(places),df_mock_scores["gmap_score"],[0] * len(df_mock_scores))



st.subheader('Social Distancing Map')

# response = requests.get('https://3u54czgyw4.execute-api.eu-central-1.amazonaws.com/default/sdd-lambda-request').text.replace("}{", "},{")
# ast.eval(response)
# json.loads(response)

st.altair_chart(alt.Chart(df_mock_scores[df_mock_scores["name"].isin(places)][["name","filtered_score"]]).mark_bar(size = 20).encode(
    x='name:N',
    y='filtered_score:Q',
    color=alt.Color('filtered_score:Q', scale=alt.Scale(scheme='greens'))
).properties(width=750,height=400))

st.pydeck_chart(pdk.Deck(
map_style='mapbox://styles/mapbox/light-v9',
initial_view_state=pdk.ViewState(
  latitude=50.32,
  longitude=9.41,
  zoom=5,
  pitch=50,
      ),
      layers=[
          pdk.Layer(
             'HexagonLayer',
             data=df_mock_scores,
             get_position='[lon, lat]',
             radius=20000,
             elevation_scale=100,
             elevation_range=[0, 1000],
             pickable=True,
             extruded=True,
          ),
          pdk.Layer(
              'ScatterplotLayer',
              data=df_mock_scores,
              get_position='[lon, lat]',
              get_color='[200, 30, 0, 160]',
              get_radius=200,
          ),
      ],
  ))

data_topojson_remote = alt.topo_feature(url=url_topojson, feature='counties')
c = alt.Chart(data_topojson_remote).mark_geoshape(
    stroke='white'
).encode(
    color=alt.Color('filtered_score:Q', scale=alt.Scale(scheme='greens')),
    tooltip=[alt.Tooltip("properties.name:N", title="City"),alt.Tooltip("filtered_score:N", title="Score")]
).transform_lookup(
    lookup='id',
    from_=alt.LookupData(df_mock_scores, 'id', ['filtered_score'])
).properties(width=750,height = 1000)
st.altair_chart(c)

if len(places) > 0:
    st.subheader("Vergleich Soziale Distanz")
    st.altair_chart(alt.Chart(df_mock_scores[df_mock_scores["name"].isin(places)][["name", "date", "filtered_score"]]).mark_line().encode(
        x= alt.X('date:T',axis = alt.Axis(title = 'Tag', format = ("%d %b"))),
        y= alt.Y('filtered_score:Q',title="Soziale Distanz"),
        color=alt.Color('name',title ="Landkreis")
    ).properties(
        width=750,
        height = 400
    ))

st.subheader("Vergleich Soziale Distanz")


if st.checkbox("Show raw data", False):
    st.subheader("Ort gefiltert")
    st.write(df_mock_scores[df_mock_scores["name"].isin(places)])