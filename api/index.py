from flask import Flask, request
from flask_restful import Api, Resource
from firebase import firebase
from flask_cors import CORS, cross_origin
from flasgger import Swagger
import numpy as np
import pickle
from pykdtree.kdtree import KDTree
import re

app = Flask(__name__)
# connect to firebase
firebase = firebase.FirebaseApplication('https://raasta-c542d-default-rtdb.asia-southeast1.firebasedatabase.app/', None)

template = {
  "info": {
    "title": "Raasta API",
    "description": "API Documentation for Raasta: An Automated Road Classification System",
  },
}
Swagger(app, template=template)

@app.route('/get_points/<TypePoints>', methods=['GET'])
def get_potholes(TypePoints):
    """
    Get specific type of points from the database.
    ---
    tags:
      - name: Points

    parameters:
        - name: TypePoints
          in: query
          type: string
          required: true
          description: A string value that specifies the type of points(Pothole, Speedbreaker).

    responses:
      200:
        description: Retrieve specific type of points in the form of latitude and longitude coordinates from a Firebase Realtime Database and display them on a map as markers.
        schema:
          properties:
            Pothole:
              type: array
              items:
                type: array
                items:
                  type: number
                  description: latitude and longitude co-ordinates
          example: [{"Pothole": [[24.9597674, 67.0627178], [24.9597674, 67.0627178]]}]
      500:
        description: Error retrieving points. Invalid type of points specified.
    """
    pothole = []
    speedbreaker = []

    if TypePoints == "Pothole":
        result = firebase.get('/pothole-locations', None)
        for key1, value in result.items():
            latlong = []
            for key2, value2 in value.items():
                latlong.append(value2)
            pothole.append(latlong)
        return({"Points" : pothole})
    
    elif TypePoints == "Speedbreaker":
        result = firebase.get('/speedbreaker-locations', None)
        for key1, value in result.items():
            latlong = []
            for key2, value2 in value.items():
                latlong.append(value2)
            speedbreaker.append(latlong)
        return({"Points" : speedbreaker})

    else:
        return({"Points" : "Invalid type of points requested"})
        
  
@app.route('/get_nearest_neighbor/<path:input>', methods=['GET'])
def nearest_neighbor(input):
  """
    Get nearest pothole from given latitude and longitudinal points. 
    ---
    tags:
      - name: Points

    parameters:
        - name: input
          in: query
          type: string
          required: true
          description: Location points that will be used to locate and return the nearest pothole location points. The value comprises of latitude and longitude pairs. Latitude co-ordinates are in the range -90, 90 and longitudal co-ordinates are in the range -180, 180.
      
    responses:
      200:
        description: Get all the nearest pothole points from the given location points

        schema:
          properties: 
            p_dist: 
              description: blah
              type: float
            
            p_loc: 
              description: blah
              type: array
              items:
                type: integer
                description: latitude and longitude co-ordinates
            
            s_dist: 
              description: blab
              type: float

            s_loc: 
              description: blah
              type: array
              items:
                type: integer
                description: latitude and longitude co-ordinates
          example: {"p_dist": 0.5195423427957768, "p_loc": [24.8029698,67.0779413],"s_dist": 0.5221990925306665,"s_loc": [24.8140999,67.0828272]}
      500:
        description: Invalid input values or invalid amount of input values provided. 
    """

  latitude_pattern = r'^[-+]?([0-8]?\d(\.\d{1,6})?|90(\.0{1,6})?)$'
  longitude_pattern = r'^[-+]?((1[0-7]|[0-9])?\d(\.\d{1,6})?|180(\.0{1,6})?)$'

  txt = input.split(',')
  txt = [element.strip() for element in txt]
  points = []
  # length should be 1, 2, or multiples of 2
  if len(txt) % 2 == 0 and len(txt) >= 2:
     p = []
     for x in range(len(txt)):
        # latitude
        if x % 2 == 0:
           if re.match(latitude_pattern, txt[x]):
                p.append(float(txt[x]))
           else:
              break
        elif x % 2 == 1:
           if re.match(longitude_pattern, txt[x]):
                points.append([p.pop(), float(txt[x])])
           else:
              break
  print(points)
  potholes = []
  speedbreakers = []
  result = firebase.get('/pothole-locations', None)
  for key1, value in result.items():
      latlong = []
      for key2, value2 in value.items():
          latlong.append(value2)
      potholes.append(latlong)

  result = firebase.get('/speedbreaker-locations', None)
  for key1, value in result.items():
      latlong = []
      for key2, value2 in value.items():
          latlong.append(value2)
      speedbreakers.append(latlong)

           
  if len(points) >= 1:
    print(points)
    p_dist, p_loc, s_dist, s_loc = [],[],[],[]

    p_tree = KDTree(np.array(potholes))
    p_dist, p_index = p_tree.query(np.array(points))
    p_loc = p_tree.data[p_index]
    s_tree = KDTree(np.array(speedbreakers))
    s_dist, s_index = s_tree.query(np.array(points))
    s_loc = s_tree.data[s_index]

    if type(s_dist) == float:
      return {'p_dist' : p_dist, 'p_loc': p_loc.tolist(), 's_dist' : s_dist, 's_loc': s_loc.tolist()}
    else:
      return {'p_dist' : p_dist.tolist(), 'p_loc': p_loc.tolist(), 's_dist' : s_dist.tolist(), 's_loc': s_loc.tolist()}
  else:
     return "Error. Please check your input."
  
@app.route('/get_intersection/<path:input>', methods=['GET'])
def intersection(input):
  """
  Get nearest pothole from given latitude and longitudinal points. 
  ---
  tags:
    - name: Points

  parameters:
      - name: input
        in: query
        type: string
        required: true
        description: Location points that will be used to locate and return the nearest pothole location points. The value comprises of latitude and longitude pairs. Latitude co-ordinates are in the range -90, 90 and longitudal co-ordinates are in the range -180, 180.
    
  responses:
    200:
      description: Get all the nearest pothole points from the given location points.
      schema:
        properties:
          Potholes:
            description: Number of potholes calculated.
            type: integer
        example: {"Potholes": 1}
    500:
      description: Invalid input values or invalid amount of input values provided. 
  """

  latitude_pattern = r'^[-+]?([0-8]?\d(\.\d{1,6})?|90(\.0{1,6})?)$'
  longitude_pattern = r'^[-+]?((1[0-7]|[0-9])?\d(\.\d{1,6})?|180(\.0{1,6})?)$'

  txt = input.split(',')
  txt = [element.strip() for element in txt]
  print(txt)
  points = []
  # length should be 1, 2, or multiples of 2
  if len(txt) % 2 == 0 and len(txt) >= 2:
    p = []
    for x in range(len(txt)):
        if x % 2 == 0:
          if re.match(latitude_pattern, txt[x]):
            p.append(float(txt[x]))
          else:
            break
        elif x % 2 == 1:
          if re.match(longitude_pattern, txt[x]):
              points.append([p.pop(), float(txt[x])])
          else:
              break
    print(points)
    potholes = []
    speedbreakers = []
    
    result = firebase.get('/pothole-locations', None)
    for key1, value in result.items():
      latlong = []
      for key2, value2 in value.items():
          latlong.append(value2)
      potholes.append(latlong)

    result = firebase.get('/speedbreaker-locations', None)
    for key1, value in result.items():
      latlong = []
      for key2, value2 in value.items():
          latlong.append(value2)
      speedbreakers.append(latlong)

    def is_between(a,b,c):
      EPSILON = 0.0001
      return np.linalg.norm(a-c) + np.linalg.norm(b-c) - np.linalg.norm(a-b) <= EPSILON

    def data_on_route(points, potholes, speedbreakers):
      p_on_route = []
      s_on_route = []
      for i in range(len(points)-1):
         for j in range(len(potholes)):
            if is_between(np.array(points[i]), np.array(points[i+1]), np.array(potholes[j])):
               p_on_route.append(potholes[j])

         for j in range(len(speedbreakers)):
            if is_between(np.array(points[i]), np.array(points[i+1]), np.array(speedbreakers[j])):
               s_on_route.append(speedbreakers[j])

      return p_on_route, s_on_route
    
    potholes, speedbreakers = data_on_route(points, potholes, speedbreakers)
    p_result = list(set(tuple(x) for x in potholes))
    s_result = list(set(tuple(x) for x in speedbreakers))

    return {"Number of potholes" : p_result, "Number of speedbreakers:" : s_result}
  else:
    return "Error. Please check your input."
