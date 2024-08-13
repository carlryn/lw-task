# Read me

## Welcome!

## Running the application
You can run the code in many ways, but it is dependent on AWS for dynamodb access & also for security manager(OpenAI API key).

### Prerequisites
I did the infrastructure part "somewhat manually", so it will take some manual work.


#### Setup dynamodb
First Install poetry. I used python 3.10, installed through pyenv (It's great).
Then run
```bash
poetry install
poetry shell
python scripts/dynamodb_setup.py
```
For this part I didn't create a docker environment.

#### OpenAI key
I decided to go with OpenAI. I will discuss this choice later, and come with alternatives. There is much to discuss :)
The key you need to set is the following:
```
openai_api_key
```

### Running the application

Docker:
1. Build the image.
2. Run the image. But since it is dependent on AWS, you will need to insert AWS credentials. You will need access to secrets manager, and dynamodb. You can set this up with IAM if needed.

Kubernetes:
In this repo there is a yaml file that can be used to deploy to Kubernetes. There is no real reason for using Kubernetes here though, I did it more for myself (practice).
I used EKS for the cluster. You need to make sure that the nodegroup you select(IAM) has access to dynamodb, and secrets manager. I did it manually myself through IAM in AWS Console. Starting an EKS cluster takes around 25-35 minutes. The rest is more or less instant.
To create an EKS:
1. Create an eks cluster. This will also create other necessary infrastructure parts(VPC, IAM, ..): eksctl create cluster --name "INSERT_CLUSTER_NAME" --region INSERT_REGION"
2. aws eks update-kubeconfig --region "INSERT_REGION" --name "INSERT_CLUSTER_NAME"
3. Make sure you have ALB running on your cluster. If it is not properly installed the ingress will not work. Read the prerequisits: https://docs.aws.amazon.com/eks/latest/userguide/alb-ingress.html

You now have the cluster setup. Now you need to add IAM policies to the nodegroup.
1. Find the IAM for your nodegroup. Add read policy for dynamodb, and secrets manager access.
3. You are good to go! ```kubectl apply -f llm-api.yaml```
4. Run the following command to get the address: ```kubectl get ingress -n llm-api```
5. Go to your browser and input the address and add ```/docs``` to the ending :)

Troubleshooting:
* If the address field is empty for the ingress: If there is no address showing for the ingress, this happened to me btw, then it is likely that the alb is not running properly. The command kubectl get pods -n kube-system should show the alb.
* Installing the alb also meant installing IAM OIDC on the EKS cluster. It will come up during the installation, and the command for installation will show.


```
aws ecr get-login-password --region REGION | docker login --username AWS --password-stdin LINK_TO_YOUR_ECR
docker build -t lw_task .
docker tag lw_task:latest LINK_TO_YOUR_ECR/lw_task:latest
docker push LINK_TO_YOUR_ECR/lw_task:latest
```

## Create a high-level conceptual & technical design of the solution and the tools you will utilise.
A part of this problem is figure out a good use case. I decided for this MVP, to take a company wanting to do advertising, and the information provided as context to the LLM to be the brand image, and also the products and specifications. To generate this data I used GPT-4o and guided it until I was happy.

The components I used:
* Promptfoo for model evaluation.
* FastAPI for the rest API.
* To build fast, I went with API Access for the LLM and Open AI(I suspect this breaks the data locality)
* For database, I decided to go for dynamoDB.
* Deployment: the API is dockerized and you can run it through kubernetes if you want :)
* Poetry for the package management


### LLM evaluation
For the evaluation I decided to use Promptfoo library, a javascript library. It supports many kinds of evaluation and also contains a dashboard to view the results :) Being to compare and view outputs from different models, or prompts next to each other makes it easier to either chose model or improve the prompts.

Information on how to install promptfoo can be found here: https://github.com/promptfoo/promptfoo
To run you need to set the following env variables:
```
OPENAI_API_KEY=YOUR_KEY
PROMPTFOO_PROMPT_SEPARATOR=ANYTHING_RANDOM_AS_LKJHIUGHUIG
```
The ```PROMPTFOO_PROMPT_SEPARATOR``` needs to be modified because of the evaluation prompt I am using.

After setting the environment variables we can run:
```
promptfoo eval --no-cache
promptfoo view # Will open the dashboard
```

I kept the evaluation quite simple, and you will only find OpenAI models (Please refer to FAQ in the end). I like the idea of having powerfull LLM models judge the output, and I believe it would be possible to take this much further than what I did. Here it would have been interesting to compare with models such as Llama 3.1 of various sizes( I had some issues with AWS Bedrock, but could use Modal see later).

I ran a manual evaluation using LLama 3 8B, and LLama 3 70B. 70B was good, 8B had a performance similar to GPT-3.5.

I also believe that incorporating a human generated dataset could be interesting:
* Could be used to improve the ML judge (I suspect)
* Can use similarity based metrics. Compare embeddings of ground truth, to the embeddings of the generated text.
* BLEU scores and more...
https://shubham-shinde.github.io/blogs/llms-metrics/#automatic-vs-human-evaluation

Given that a human generated dataset is created, we could also finetune the models. Finetuning models can allow us to use a smaller cheaper model, with performance of a bigger model. Often examples are given to LLMs and this increases the number of tokens. Finetuning could remove that need :)

### How would you proceed to scale your model (to support for new parameters and languages)
A strong evaluation is important, and the automatic(LLM Judge) can be reused directly.
Languages we might not understand ourselfs, so maybe we can translate using the most powerfull model, and have a translater to make sure quality is good. For western languages multilingual capabilties tend to be strong, but beware of asian languages, or other languages that will not have an overlap in the tokenization to western languages. Especially if you finetune, since the model can easily overfit to language in these cases.


### Can you provide a strategic roadmap with ideas/techniques to uplift the performance of the overall system.
From a model perspective:
1. More prompt engineering, and a much more thorough evaluation. I would also use human generated examples. Improved models are released on a weekly level, and it should be easy to evaluate new models. Make more examples of different domains or verticals.
* Guardrails: Make sure the model is not used in the "wrong" ways. To check for prompt injections, and possibly content we do not want the models to generate.
* Finetuning of the LLM, or providing examples.
* RAG based solution if we have a lot of information on a customer.


ML Ops:
* Mainly cost related. I go through this part thoroughly later.



#### What you would do if you were to optimize training and inference speed.

##### Training
As you noticed there is no training going on here, but let's put a few words on it anyways.

Finetuning for LLMs is mainly done with QLoRA or LoRA. The LoRA part approximates larger matrixes with two smaller, and the Q part quantizes these to lower precision, reducing memory. It's old concepts put into LLMs. The fastest is LoRA, memory reduction techniques and speedups does not always come hand in hand.
What I'm reading is that LoRA is slightly faster than a full finetuning

Another obvious candidate is just increasing the flops. Get a more powerfull GPU, or multiple GPUs.

##### Inference

What does speed mean? I will divide this into latency & throughput

#### Latency
What impacts latency:
* Size of model.
* Some optimizations on the model(graph optimization, maybe more).
* Quantization can also reduce depending if the serving framework supports it. E.g vLLM does not provide a speedup for AWQ while TGI does.
* Batch size, more on this later.
* GPU

#### Throughput
This kind of blew up, but more information is usually good :)
##### Self-hosting
Serving LLMs is not cheap, because the GPU's required are expensive.

The following blogpost is very informative, and the vLLM paper is a recommended read. Especially the graph showing batch size RAM and throughput tells the story.
https://blog.vllm.ai/2023/06/20/vllm.html

Batch size does increase throughput massively, but with it latency also increases. I ran some experiments myself on 3B model with vLLM(A100 40GB). 1 query in 3 seconds, 60 queries(2k tokens/sec generation) in 8 seconds.

A competitor to vLLM is TGI. In my experience TGI it is easier to use, supports more features such as AWQ, but it is not as fast as vLLM.

Other frameworks include llama.cpp, ollama. However, these do not support continues batching(significant downside). Continues batching is similar to normal ML batching techniques, but in a real-time setting. As requests come in they are directly computed, even though the LLM is already computing other requests. In more "traditional" ML the new request would be blocked until the request being computed would finish. This increases the max throughput considerably.

##### Interesting! But how do I choose my setup? :D
This would be my recommendation:
1. I'd pick vLLM as my inference engine (if you at least have A100 40GB) available. If you don't you might need to pick TGI and use a quantized model(AWQ). Then choose A10G 25GB. AWS will not easily provide you with good GPUs :') If this is you, then look in the Modal section, and be set free from the claws of AWS.
2. Select a number of input tokens, number of output tokens and max latency.(10 seconds in your example)
3. Now you need to tune. Select GPU and see how many concurrent request you can handle while being below the latency requirements. Obviously, cost will be a consideration.


##### API Access
Multiple variants exist. Obviously region will be a limiting factor. Some thoughts & providers:
* Together.ai provides many open source models.
* With Huggingface endpoints you can deploy directly to your account, choose a model from the hub and also the GPU(they even have A100 GPUs for AWS).
* Amazon Bedrock has many models, but they only support a few LLMs. You can pay per token, or pay for units if you have a higher throughput.
* API Access is the easiest way to ensure a low latency. This is a great website for benchmarking: https://unify.ai/benchmarks


##### Choosing between self-hosting and API Access
It's a question of throughput, and maybe also security concerns.
For offline work where the throughput will be high and latency is less of a concern, self-hosting will be hard to beat on cost.
For real-time with low latency you have make a good case for self-hosting. There is a cost to deal with the MLOps (or LLMOps), and you need a good amount of throughput to deliver generation at a lower price than API Access. Your GPUs need to work for their cost.



##### Auto-scaling
API Access will always scale, but if you opt for self-hosting then you need to consider a few things:
* LLMs are big. You can't download them every time you start a pod, then it could take minutes to start them. Two other options I see. Put the LLM in the docker image(modal style) or have a shared disk the pods can load the model from.
* Loading parameters from disk takes time, and you also need to start the inference serve(engine). In my experience this takes 20s - 1m 30s depending on the size of the model(2B - 70B). If you can't start your servers fast enough, maybe you should have API access as a backup to deal with the bursts. If you send a larger and larger number of requests to your LLM deployment, without scaling fast enough, first your latency will start to increase and then they could possibly run out of memory and crash(worst case). Hopefully, you will let requests wait, or timeout instead of crashing :)
* Worth mentioning is that ollama is using GGUF. You start ollama servers in a few seconds, but I would not recommend this setup.

## FAQ

#### What about GDPR and data locality?
Yes, it is true. OpenAI does not allow you to choose region. However, I do provide multiple examples on self-hosting vs API access which does solve for this.

#### What is Modal, and what is the modal_deployment.py in scripts folder?
Great question!
They provide decently priced GPU's, lightning fast starts and a good dashboard. The file can be used to deploy Llama 3.1 8B on their platform. I considered using this to show self-hosting. I am a fan. Read more on their website. https://modal.com/


