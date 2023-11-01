# Developer Docsing

```txt
app/
├── models/ # 模型层, 数据库模型等
├── views/ # 视图层, 处理请求和返回响应
├── controllers/ # 控制器层, 业务逻辑处理
└── main.py # 程序入口
```

在 `views` 中主要处理接口的参数传递, 在主控 `controllers` 中主要处理业务逻辑, 一般有一个类似Runtime的主线程来分布控制业务的关于线程的参数。

<style>
  .container {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
  }
</style>
<div class="container">
  <center>
      <img src="https://p.qlogo.cn/bizmail/r8By5VdJGYJqib9WwmWLNNZeVGmtiafeLM3v9lqxxaNZm60P9AAXU8cw/0" />
      <h3>宁波职业技术学院知识库 开发文档</h3>
      <p>Ningbo Polytechnic knowledge base development doc.</p>
    </center>
</div>







## 项目介绍

宁波职业技术学院（以下简称“宁职院”）为项目 **NbptGPT（宁职院生成式问答模型）**提供万亿规模数据快速检索与精确查询等服务。

在LLM（大型语言模型）人工智能问答系统中，知识库的重要性不可忽视，它在多个方面对系统的性能和功能产生重大影响。



### 相关概述

-  **提供信息支持：**知识库是系统的信息存储和检索中心。它包含了广泛的知识、事实和数据，可以用来回答用户的问题。没有知识库，系统将无法为用户提供有用的答案，从而失去了其主要目标，即提供信息支持。
    知识库可以存储历史和背景信息，使系统能够理解和回答与特定主题或事件相关的问题。这对于提供全面的答案以及为用户提供更多上下文信息非常重要。
-  **提高准确性：**知识库可以用来验证模型生成的答案的准确性。通过将模型生成的答案与知识库中的信息进行比对，可以减少错误答案（幻觉）的出现，并提高系统的准确性。知识库还可以用来纠正模型可能的误解或误解用户问题的情况。
    知识库中的信息是可验证的，用户可以参考它们来验证系统提供的答案的正确性。这增加了系统的可信度和可靠性。
-  **支持多领域问题：**知识库可以涵盖多个领域的信息，使系统能够回答各种类型的问题。这意味着系统不仅可以处理通用性问题，还可以应对特定领域的问题，从而增强了其适用性和实用性，后续拓展企业内部或相关机关的内部信息的检索。
-  **支持复杂问题解答：**一些问题可能需要深入的知识和复杂的推理过程才能回答。知识库可以提供系统所需的材料和信息，以支持这种复杂性，从而提高系统的问题解答能力。
-  **帮助训练学习：**知识库不仅对于回答问题是重要的，还对于系统的学习过程至关重要。系统可以通过分析和理解知识库中的信息来改进其回答质量，并逐渐增加自己的知识。



### 组成部分

**数据库** (规划性)

在知识库系统开发时使用非关系数据库（MySQL）进行用户的数据存储，通常来说非向量检索的目标都将使用数据库进行存储。

**知识库**

存储宁职院相关的信息和数据，如学校简介、专业介绍、教师资料、课程安排等。知识库采用文档词表进行设计，并且构建[向量检索系统](#模型检索开发 )。

**模型检索**

用于对知识库的内容进行相似检索，根据用户的查询语句，返回最相关的文档或段落。基于深度学习的文本匹配模型，可以利用预训练的语言模型来提取文本的语义特征，并计算文本之间的相似度。

**鉴权接口**

用于对用户进行身份验证和授权，保证知识库的安全性和可信度。鉴权接口是一个基于 OAuth 2.0 协议的标准接口，可以支持多种类型的客户端应用，如网页应用、移动应用、桌面应用等。鉴权接口可以利用第三方服务提供商（如企业微信、微信等）来实现用户的登录。

在后续业务拓展中提供端到端的能力，降低接入门槛。





## 知识库内容结构

知识库（数据库）所包含的信息以下做两大分类，长效信息、短效信息。
知识库内容存储基于 `FAISS` 实现，且每一条知识的结构如下：

```python
{
	"page_content": "", # str 信息内容，不能为空
    "metadata": {
        "id": 0, # int 数据唯一标识
        "splitter": "default", # str 分割器标识
        "model": [], # EmbeddingModelManager -> List[str] 检索模型
        "tag": [], # TagManager -> List[str] 标签管理
        "related": False, # bool 是否被切分，用于匹配动态切分的标识
        "start_time": 0, # int 开始生效时间，时间戳
        "valid_time": 3600, # int 数据生效的时间，时间戳，-1为长效信息
    } # Namespace | Object
}
```



### 内容概述

#### 长效信息

长效信息包括且不限于学生手册、学校简介、学校简介、专业介绍这部分内容比较容易嵌入模型，通过微调进行模型输出层的训练。

长效信息的增删改查，需要一定的权限，这部分内容的变更将直接导致LLM的理解偏差和幻觉现象，使用模型的**增强训练**去补偿损失。

##### 额外的存储文档格式

因为长效信息不易修改等特点，根据 [tatsu-lab/stanford_alpaca](https://github.com/tatsu-lab/stanford_alpaca) 的格式进行转换，采用 [多标签 (mulit labels)](#多标签 (mulit labels)) 的方式格式化，以便进行数据整理和模型微调。

>    注意：该数据存储的方式为规划性，暂不于程序中实现



#### 短效信息

短效信息有短期通知、教师资料、课程安排，短期的变更，这类信息具有重置和恢复的可能存在，用于模型输入的方式短效学习。

该信息，需要明确生效时间，生效时间也做权重比较，向下覆盖旧的相似信息，并且只取生效期间内的数据。
如果多个数据生效时间处于交集，则取较晚结束（较新）的内容。





## 应用接口开发

为了强化该服务的健壮性和可持续发展，该项服务将同步开发应用接口为 **“应用客户端”、“授权服务商”、“授权企业微信”** 提供对接接口。

接口包含但不限于请求返回、信息上报、知识库管理

### 请求握手

#### 请求参数

参见《企业微信 开发者文档 第三方应用鉴权》





### 知识库内容检索

接口信息：`/api/query` `["GET", "POST"]`

请求参数如下：

| 参数（*为必传参数） | 描述                                                     |
| :------------------ | -------------------------------------------------------- |
| ***search**         | 字符串，搜索用的字符串                                   |
| result_type         | "json" \| "txt" \| "jsonl"，返回的内容格式，默认: "json" |
| iterations          | 数字，内容迭代轮次，默认: 1                              |
| model               | 字符串，强制使用的检索模型，默认: "default"              |



#### 返回参数

| 参数 | 描述                 |
| :--- | -------------------- |
| code | 数字，返回码         |
| msg  | 字符串，返回附带信息 |
| data | 列表，内容见下：     |

```python
{
	"page_content": "", # str 信息内容，不能为空
    "metadata": {
        "id": 0, # int 数据唯一标识
        "splitter": "default", # str 分割器标识
        "model": [], # EmbeddingModelManager -> List[str] 检索模型
        "tag": [], # TagManager -> List[str] 标签管理
        "related": False, # bool 是否被切分，用于匹配动态切分的标识
        "start_time": 0, # int 开始生效时间，时间戳
        "valid_time": 3600, # int 数据生效的时间，时间戳，-1为长效信息
    } # Namespace | Object
}
```





### 知识库信息上报

#### 奖励上报

这个接口一般用于，检索信息的 **错误/加强** 的上报，用于收集信息以提高准确率。

接口信息：`/api/support/reward` `["GET"]`

请求参数如下：

| 参数（*为必传参数） | 描述                                           |
| ------------------- | ---------------------------------------------- |
| ***location**       | 字符串，错误的定位，一般为应用中错误发生的地址 |
| remark              | 字符串，备注，默认为空                         |



#### 错误上报

这个接口一般用于，检索信息的 **错误/加强** 的上报，用于收集信息以提高准确率。
接口信息：`/api/support/error` `["GET"]`

请求参数如下：

| 参数（*为必传参数） | 描述                                           |
| ------------------- | ---------------------------------------------- |
| ***location**       | 字符串，错误的定位，一般为应用中错误发生的地址 |
| remark              | 字符串，备注，默认为空                         |



#### 返回参数

| 参数 | 描述                 |
| :--- | -------------------- |
| code | 数字，返回码         |
| msg  | 字符串，返回附带信息 |

#### 



### 知识库内容管理

这个接口用于对知识库数据的直接管理，这部分的鉴权将由**企业微信**的权限替代。



#### 增加信息

接口信息：`/api/edit/add` `["GET"]`

请求参数如下：

| 参数（*为必传参数） | 描述                                                        |
| ------------------- | ----------------------------------------------------------- |
| ***data**           | 字符串（JSON），传入对象，具体参见[下文](#参数 `data` 说明) |
| remark              | 字符串，备注，默认为空                                      |

##### 参数 `data` 说明

需要传入 **JSON** 的数据格式，即为：

```python
{
	"page_content": "", # str 数据内容
    "metadata": {
        "tag": [], # List[str] 标签列表
        "model": ["default"], # EmbeddingModelManager -> List[str] 知识检索器
    }
}
```

注意，在传入 `data` 的时候，`metadata.id` 会自增，所以可忽略。



#### 删除信息

接口信息：`/api/edit/delete` `["GET"]` 

请求参数如下：

| 参数（*为必传参数） | 描述                                                        |
| ------------------- | ----------------------------------------------------------- |
| ***data**           | 字符串（JSON），传入对象，具体参见[下文](#参数 `data` 说明) |
| remark              | 字符串，备注，默认为空                                      |

同 **增加信息** 中的格式一样，所带有的参数均会被视为匹配条件，不能为空



#### 更改信息

接口信息：`/api/edit/update` `["GET"]` 

请求参数如下：

| 参数（*为必传参数） | 描述                                                        |
| ------------------- | ----------------------------------------------------------- |
| ***data**           | 字符串（JSON），传入对象，具体参见[下文](#参数 `data` 说明) |
| remark              | 字符串，备注，默认为空                                      |

条件较为苛刻，对 `data` 信息完全匹配的项目做修改。

**注意：`metadata.model` 中规定了该数据只能被 `["default", "..."]` 检索到**



#### 返回参数

| 参数 | 描述                 |
| :--- | -------------------- |
| code | 数字，返回码         |
| msg  | 字符串，返回附带信息 |





## 模型检索开发 

检索模型，主要完成 **segment to documents** 的功能，根据句义对词表进行检索，获取相似度高或关联性较强的内容。

受到多注意力机制 [FlashAttention](https://github.com/Dao-AILab/flash-attention) 的启发，操作词表对内容进行线性变换后分块，在相同 `chunk_size` 下的检索能力是有一定变化的，这里以 [text2vec-large-chinese](https://huggingface.co/GanymedeNil/text2vec-large-chinese) 为例，在 `batch` 大小接近的时候模型表现优异，在与模型训练的 `batch` 大小差距越大时表现越差，所以在对 `vector` 进行检索的时候使用动态的 `chunk_size` 调整的方式进行数据检索。

实现[多头多模](#多头多模)（多模型任务）的知识库检索方案，在不同知识下使用不同的检索模型对该领域下再次进行迭代检索，这样以提高知识库检索的准确性，以及拓展检索面积。

多模的交叉验证，这里通常使用垂直领域检索模型进行交叉验证，所得的数据将以 `jsonl` 存储，根据 `loss` 打分并相应排序以增强训练。



### 索引分片

读取在配置的知识库路径下的所有分片信息，在保存索引时遵循 **标签顺位命名** 的规范。

#### 标签顺位命名

若上一条知识的 `tag[0]` 本条也存在，那么将本条顺位与上一条信息一同被分片命名。



### 贪婪检索和非贪婪检索

在进行知识库检索时遵循，在同等检索条件下进行检索时支持 **贪婪** 与 **非贪婪** 的检索方式：

#### 贪婪检索

未达到必要条件将一直向外拓展检索，即为：向上和向下检索到 `related: False` 为止。

例如：

```json
[
    ...
    {
        "page_content": "文档三",
        "metadata": {
        	...
            "tag": ['电子信息工程学院', '团校活动一'],
            "related": False,
			...
        }
    },
    // 无法向上匹配
    {
        "page_content": "文档四",
        "metadata": {
        	...
            "tag": ['电子信息工程学院', '团校活动一', '学生手册'],
            "related": True,
			...
        }
    },
    {
        "page_content": "文档五",
        "metadata": {
        	...
            "tag": ['电子信息工程学院', '团校活动一'],
            "related": True,
			...
        }
    },
    // 无法向下匹配，且能匹配到"文档五"是因为 "文档四.tag" 包含了 "文档五.tag"
    {
        "page_content": "文档六",
        "metadata": {
        	...
            "tag": ['电子信息工程学院', '团校活动一'],
            "related": False,
			...
        }
    },
	...
]
```

#### 非贪婪检索

不 向上 或 向下 进行检索拓展，并且提供，规划性接口：

-   支持漫游检索 (beta)

>   漫游检索作为非贪婪检索依旧不支持拓展检索，但为了完成 相对较 泛 的搜索，会逐级降低检索阈值，进行现有内容合并迭代的检索



### 部分向量模型列表

>   class EmbeddingModelManager().get_embedding_models() -> List[Dict[str, EmbeddingModel()]]

| 模型                                                         | 描述                                                         | 键           |
| ------------------------------------------------------------ | ------------------------------------------------------------ | ------------ |
| BAAI/bge-large-zh                                            | 对通用中文的进行语义匹配                                     | default      |
| [text2vec-large-chinese](https://huggingface.co/GanymedeNil/text2vec-large-chinese) | 对通用中文的进行语义匹配                                     | default_1    |
| text2vec-small-vocational                                    | 对职业教育的内容匹配，以职业教育为例，具体参见 [面向职业教育领域的句子语义相似度模型研究](#) | vocational   |
| [text2vec-base-multilingual](https://huggingface.co/shibing624/text2vec-base-multilingual) | 多语言匹配模型，用CoSENT方法训练                             | multilingual |
| [text2vec-base-chinese-sentence](https://huggingface.co/shibing624/text2vec-base-chinese-sentence) | 对通用中文句子进行语义匹配                                   | sentence     |





<div style="page-break-after: always;"></div>

## 附录

### 模型容错增量训练

这个概念其实和奖励模型很像，但是我在这里引出其实是针对宁职院的问答垂直领域的，通过研究得出，模型在 `few-shot` 的表现直接影响到模型的准确率（也称“**得分**”）而基于知识库的问答模型在领域的注意机制的能力欠缺而出现的准确性低的问题，这里有几个解决方案的设想：

-   对数据集进行更高强度的 `prompt` 规范，保证通用领域的对齐税最低。
-   多头的二分类奖励模型参与监督的训练方法。



### 多头多模

在知识库输入的步骤就制定使用的检索模型进行多轮迭代检索。使用通用检索，后对内容再次进行垂直的模型检索，获取的非己知识内容与输入的 `loss` 代表通用检索准确率的取反，这样获取到的数据的准确率会大大提升，同样这个算法也能用于模型的微调。

>   这里是一个设想，在需要完成多模任务的时候，使用多个实例进行相互监督完成任务。
>
>   那么，在接口通信时需要使用一个主线程的 controller 进行调控，而在原有的开发计划中无需实现多线程的检索任务，在规划性任务中，将于每个 `src.model` 实例时提供一个线程的 **中间件 (middleware)** 进行单线程外的调控，这样就从 主线程的 controller 对不同线程进行分发实现“多线程”，但是这对于程序的运行效率没有任何帮助。



### 多标签 (mulit labels)

在 [tatsu-lab/stanford_alpaca](https://github.com/tatsu-lab/stanford_alpaca) 中的数据集单样例中 `input` 为字符串，**mulit labels** 使 **input** 为一个**列表**，且不允许为空，如下：

```json
[
    {
        "instruction": "Give three tips for staying healthy.",
        "input": ["EOF1", "EOF2", "EOF3"],
        "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."
    }
]
```



<div style="page-break-after: always;"></div>

<center><h3>部分参考</h3></center>

1.   [Dao-AILab/flash-attention: Fast and memory-efficient exact attention (github.com)](https://github.com/Dao-AILab/flash-attention)
2.   [shibing624/text2vec: text2vec, text to vector. (github.com)](https://github.com/shibing624/text2vec)
3.   [tatsu-lab/stanford_alpaca: Code and documentation to train Stanford's Alpaca models, and generate the data. (github.com)](https://github.com/tatsu-lab/stanford_alpaca)
4.   https://github.com/huggingface/transformers/blob/ef10dbce5cbc9a8b6a0a90b04378ca96f4023aa1/src/transformers/trainer.py
5.   [[2107.09278\] Sequence Model with Self-Adaptive Sliding Window for Efficient Spoken Document Segmentation (arxiv.org)](https://arxiv.org/abs/2107.09278)
6.   [langchain-ai/langchain:  Building applications with LLMs through composability (github.com)](https://github.com/langchain-ai/langchain)
7.   [[2202.05262\] Locating and Editing Factual Associations in GPT (arxiv.org)](https://arxiv.org/abs/2202.05262)
8.   [microsoft/autogen (github.com)](https://github.com/microsoft/autogen)



<div align="right">最后编写于2023/10/18 23:57</div>



