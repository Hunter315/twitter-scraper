# twitter_scraper

 - POST endpoint
```https://djxjqh6uo1.execute-api.us-west-2.amazonaws.com/Prod/scrape```
body JSON: 
`{
"handle": {handle:string}
}`

The post endpoint will take some time to reflect in the get endpoints. The API Gateway operates asynchronously to avoid a timeout error and allows for the client to not wait for a reponse.
- GET by handle
```https://djxjqh6uo1.execute-api.us-west-2.amazonaws.com/Prod/user/{handle}/profile_pic```

- GET All handles (paginated, kind of) default count=10
```https://djxjqh6uo1.execute-api.us-west-2.amazonaws.com/Prod/users?count=4```

*I unfortunately didn't have the time as of uploading this to finish implementing my pagination, but the scaffolding is there.*

## How Does It Work??
One idea behind getting content from a site without using an integrated or 3rd party API is scraping the data with a web driver. Obviously an API would be way more ideal for this task, since the scraper poses a few challenges:
- Scraping takes time.
- Hosting a webdriver in the cloud can be tricky to scale.
- Scraping can break due to page DOM strcture changing without warning.
- Since it is necessary to work asynchronously, the client will not get an immediate response of success or failure.
            
I *somewhat* addressed these in my small-scale application, given the short amount of time I had. I will explain what I did and why, and how I would improve upon it going forward.

So I call to a Lambda function which scrapes the data and stores it in **DynamoDB**.
Our data is pretty non-relational and unstructured, so I opted for a NoSQL DB. This allows for fast access handling large volumes, easy scalability (sharding, partitioning, etc), and it is flexible. An SQL storage would be fine, but Dynamo works pretty well in this scenario. You can also have local instances of DynamoDB which help local development.

## Structural Choices (**local development** answer here)
I used AWS SAM for the first time to build this project. I have used CDK in the past, but since this is a fairly simple task, AWS SAM was a bit more lightweight which seemed to fit the bill.  Using SAM I also opted for image uploading with Docker as opposed to ZIP upload. This comes with some trade-offs; I have worked with webdrivers in the past and versioning can be a real pain. Docker images can be distributed more easily across teams, allows for a pretty consistent development environment in all stages of development local -> production, and allows developers to add dependencies that are customized to needs of each Lambda Function. 

But this means a bit more complexity is added in the process with containerization concepts. Build times can be affected negatively, images are ususally larger than ZIP packages, and probably a few other trade-offs. Either way works fine for our use here though. 

For **further local development** optimization, a team could opt to use more environment variables so they don't have to deploy a lambda for minor changes. Lambdas can also be cached locally for development. I don't have a lot of experience setting this up, but I read some good documentation on it here: https://aws.amazon.com/blogs/compute/caching-data-and-configuration-settings-with-aws-lambda-extensions/

## Linting and Formatting
This is an interesting idea for me, since my use of AWS has been mainly in Typescript with custom engineering-wide linters/formatters.
For Python development, a team could opt to use 3rd party integrations to achieve these goals. Something like this *might* work upon first inspection: https://github.com/awslabs/aws-lambda-powertools-python

Another important step could be to integrate a check (like Github Actions) which runs a linting test against a PR, among other tests. 

## System Design
The simplest design is as follows:

![twitter_scraper_mvp_fixed](https://user-images.githubusercontent.com/35641380/226259566-748fa9f6-e702-40f6-a2d0-2002e6f13584.png)

API Gateway calls to a webdriver ina lambda function, which calls to the db.
There are many problems with this setup, and it is the setup which my code reflects currently. First, I must make the API Gateway Event asynchronous, otherwise it will time out at 29 seconds. That means that a handle can be submitted without the client knowing when/if the transaction actually succeeded.

Here is a quick proposal to scale this project up a little bit more to handle more traffic and errors. The blue parts in particular are the changes made that we can discuss.

![twitter_scraper_v2](https://user-images.githubusercontent.com/35641380/226260307-2f67ce82-f9fa-4727-a027-28dee1466d5b.PNG)


