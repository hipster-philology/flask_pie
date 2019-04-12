# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


setup(
      name="flask_pie",
      version="0.0.1",
      author_email="leponteineptique@gmail.com",
      packages=['flask_pie'],
      package_data={},
      description="Web API for NLP tagger PIE",
      author="Thibault Clérice",
      install_requires=['nlp-pie==0.2.2', 'flask']
)
