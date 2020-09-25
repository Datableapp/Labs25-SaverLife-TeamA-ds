![MIT](https://img.shields.io/badge/license-MIT-green)
[![Python](https://img.shields.io/pypi/pyversions/FastAPI)](https://www.python.org/downloads/release/python-380/)

# Saver Life Demo Video
https://youtu.be/AMusXTNxZqs

# README Directory

- [Important Links](#important-links)

- [Contributors](#contributors)

- [Getting Started](#getting-started)

- [File Structure](#file-structure)

- [Wireframe](#wireframe)

- [Engineering Architecture Diagram](#engineering-diagram)

- [Application Overview](#application-overview)


# Important Links:
- [Deployed Application](https://a.saverlife.dev/)

- [Data Science API](http://saverlife-a.eba-atdfhqrp.us-east-1.elasticbeanstalk.com/)

- [Data Science Github](https://github.com/Lambda-School-Labs/Labs25-SaverLife-TeamA-ds)

- [Front-End Github](https://github.com/Lambda-School-Labs/Labs25-SaverLife-TeamA-fe)

- [Back-End Github](https://github.com/Lambda-School-Labs/Labs25-SaverLife-TeamA-be)

 
# Contributors
|[Doug Cohen](https://github.com/dougscohen)                                   |[Kyle Yates](https://github.com/KyleTy1er)                                        |[Harrison Kang](https://github.com/HKang42)                    |
|:-----------------------------------------------------------------------------------------------------------: | :-----------------------------------------------------------------------------------------------------------: | :-----------------------------------------------------------------------------------------------------------: |         
|                      [<img src="https://avatars1.githubusercontent.com/u/60849521?s=460&u=1c0422c701fc566ecd9edcea912801a88f1ce720&v=4" width = "200" />](https://github.com/dougscohen)                       |                      [<img src="https://avatars0.githubusercontent.com/u/53956594?s=460&u=c75a90473ca33926d32e1bca8fb1746020e3ab23&v=4" width = "200" />](https://github.com/KyleTy1er)                       |                      [<img src="https://avatars1.githubusercontent.com/u/60892706?s=460&u=9073df1aca64fdc8b216ab84b234de8ee437ec4e&v=4" width = "200" />](https://github.com/HKang42)                       
|                 [<img src="https://github.com/favicon.ico" width="15"> ](https://github.com/dougscohen)                 |            [<img src="https://github.com/favicon.ico" width="15"> ](https://github.com/KyleTy1er)             |           [<img src="https://github.com/favicon.ico" width="15"> ](https://github.com/HKang42)
| [ <img src="https://static.licdn.com/sc/h/al2o9zrvru7aqj8e1x2rzsrca" width="15"> ](https://www.linkedin.com/in/dougcohen3/) | [ <img src="https://static.licdn.com/sc/h/al2o9zrvru7aqj8e1x2rzsrca" width="15"> ](https://www.linkedin.com/in/kyle-tyler-b50a1b169/) | [ <img src="https://static.licdn.com/sc/h/al2o9zrvru7aqj8e1x2rzsrca" width="15"> ](https://www.linkedin.com/in/harrison-kang/) 

# Data Science API
The Data Science API for the SaverLife project can be found [here](http://saverlife-a.eba-atdfhqrp.us-east-1.elasticbeanstalk.com/) (hosted on AWS Elastic Beanstalk)

# Getting Started

Navigate to [http://saverlife-a.eba-atdfhqrp.us-east-1.elasticbeanstalk.com/](http://saverlife-a.eba-atdfhqrp.us-east-1.elasticbeanstalk.com/) in your browser

![image](https://user-images.githubusercontent.com/53956594/94050429-1bfbf500-fd8b-11ea-9dc8-508cca5d1270.png)

You'll see our API documentation:

- App title
- API description
- An endpoint for POST requests, `/future_budget`, `/moneyflow`, and `/spending`
- An endpoint for GET requests, `/current_month_spending` and `/dashboard`

Click the `/future_budget` endpoint's green button.

![image](https://user-images.githubusercontent.com/53956594/94050431-1bfbf500-fd8b-11ea-80f9-073c82fbf922.png)

You'll see the endpoint's documentation, including:

- The function's docstring
- Request body example, as [JSON](https://developer.mozilla.org/en-US/docs/Learn/JavaScript/Objects/JSON) (like a Python dictionary)
- A button, "Try it out"

Click the "Try it out" button.

![image](https://user-images.githubusercontent.com/53956594/94050432-1c948b80-fd8b-11ea-8fd3-a540e96b9d8b.png)

The request body becomes editable. 

Click the "Execute" button. Then scroll down.

![image](https://user-images.githubusercontent.com/53956594/94050433-1c948b80-fd8b-11ea-8cc5-121d05384331.png)

You'll see the server response, including:

- [Code 200](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/200), which means the request was successful.
- The response body, as [JSON](https://developer.mozilla.org/en-US/docs/Learn/JavaScript/Objects/JSON), which shows the recommended budget for a specific user.

## File structure

```
project
├── Dockerfile
├── requirements.txt
└── app
    ├── __init__.py
    ├── main.py
    ├── helpers.py
    ├── user.py
    ├── api
    │   ├── __init__.py
    │   ├── dashboard.py
    │   ├── predict.py
    │   └── viz.py    
    └── tests
        ├── __init__.py
        ├── test_main.py
        ├── test_predict.py
        └── test_viz.py
```

# Wireframe

![image](https://user-images.githubusercontent.com/53956594/94050435-1c948b80-fd8b-11ea-828b-6373474f1296.png)

# Engineering Diagram

![image](https://user-images.githubusercontent.com/53956594/94167940-f1b93e80-fe41-11ea-9044-0e1f1b5b9ff8.png)


## Tech stack
- [AWS Elastic Beanstalk](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/Welcome.html): Platform as a service, hosts your API.
- [Docker](https://www.docker.com/blog/tag/python-env-series/): Containers, for reproducible environments.
- [FastAPI](https://fastapi.tiangolo.com/): Web framework. Like Flask, but faster, with automatic interactive docs.
- [Plotly](https://plotly.com/python/): Visualization library, for Python & JavaScript.
- [Amazon RDS](https://aws.amazon.com/rds/): Cloud based relational database.
- [Statsmodels](https://www.statsmodels.org/): Statistical modeling library for Python.


# Application Overview

Watch the video below to see an overview of the finished product!

[![Watch the video](https://user-images.githubusercontent.com/53956594/94175252-4ad9a000-fe4b-11ea-93f2-7a2d476036f1.png)](https://youtu.be/6XMpoLHjGBQ)
