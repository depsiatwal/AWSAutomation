
from collections import namedtuple

Endpoint = namedtuple('Endpoint',['name','host','zone'])

region_to_endpoint = { 'eu-west-2': Endpoint('EU (London)','s3-website.eu-west-2.amazonaws.com','Z3GKZC51ZF0DB4')
}

def known_region(region):
    """ Returns true is this a know region """
    return region in region_to_endpoint

def get_endpoint(region):
    """ returns an endpoint"""
    return region_to_endpoint[region]
