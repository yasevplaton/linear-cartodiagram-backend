
'''

The script for the distribution of data from the table of flows of goods through the transport network graph

'''


# import necessary modules
import pandas as pd
import geopandas as gpd
import os.path
import io
from tools import tools
import datetime

from flask import Flask, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/upload_data', methods=["GET", "POST"])
def distribute_data_on_graph():

    if request.method == "POST":

        # get data
        data = request.data

        # decode data
        init_table = io.StringIO(data.decode('utf-8'))

        # set path to data directory
        # path to data directory at localhost for testing purposes
        data_dir = "data/"

        # path to data directory in production
        # data_dir = '/home/yasevplaton/linear-cartodiagram-backend/data/'

        # read files
        roads = gpd.read_file(os.path.join(data_dir, "roadsVolga.geojson"))
        points = gpd.read_file(os.path.join(data_dir, "pointsVolga.geojson"))
        lut = pd.read_csv(os.path.join(data_dir, "look_up_table_Volga.csv"), sep=",", index_col="OBJECTID")
        flow_table = pd.read_csv(init_table, sep=",")

        print('Data was loaded')
        time1 = datetime.datetime.now()
        print(time1)

        roads = roads.to_crs({'init': 'epsg:3857'})
        points = points.to_crs({'init': 'epsg:3857'})

        # convert flow table to array of correspondence matrixes
        matrix_array = tools.to_matrix_array(flow_table, lut)

        print('Matrixes have been created')
        time2 = datetime.datetime.now()
        print(time2)
        print(time2 - time1)

        # add additional fields to roads table
        # roads["src"] = 0
        # roads["dest"] = 0
        # roads["length"] = roads.length

        # bind points to roads
        # roads = tools.bind_points_to_lines(points, roads)

        # collect types of goods
        goods = tools.collect_goods_types(matrix_array)

        # create oriented multigraph and fill it with edges from roads
        net = tools.create_graph(goods, roads)

        # determine the affiliation of a node to a city
        net = tools.add_city_affiliation_attr(points, net)

        # distribute values of flows of goods on graph's edges
        net = tools.distribute_values_on_graph(net, goods, matrix_array)

        print('Values have been distributed on graph')
        time3 = datetime.datetime.now()
        print(time3)
        print(time3 - time2)

        # create dataframe from multigraph
        edges_df = tools.create_dataframe_from_graph(net, goods)

        # create geodataframe by merging dataframe and roads geometry
        road_geometry = roads[['ID_line', 'geometry']]
        edges_df = edges_df.merge(road_geometry, on='ID_line')
        geo_edges = gpd.GeoDataFrame(edges_df, crs=roads.crs, geometry='geometry')

        # reverse order of nodes in line if a first node in line is not a source node
        geo_edges = tools.reverse_nodes_order(geo_edges, points)

        # reproject edges to 4326
        geo_edges = geo_edges.to_crs({'init': 'epsg:4326'})

        print('GeoEdges Dataframe has been created')
        time4 = datetime.datetime.now()
        print(time4)
        print(time4 - time3)

        return geo_edges.to_json()

    else:

        return 'oops, something went wrong'


if __name__ == '__main__':
    app.run()
