<center>
<img width="50%" src="./assets/KnowledgeBase.png" />
<h3 style="font-size:36px;">📃知识库管理系统</h3>
</center>

基于 ChatGLM 与 Langchain 实现，开源、可离线部署的轻量文档管理与检索文档方案。

<hr />

### 目录

- [目录](#目录)
- [介绍](#介绍)
- [快速上手](#快速上手)
  - [1. 环境配置](#1-环境配置)
  - [2.模型下载](#2模型下载)
  - [3.初始化知识库和配置文件](#3初始化知识库和配置文件)
  - [4.启动项目程序](#4启动项目程序)
  - [5.注意事项](#5注意事项)

### 介绍

💡 受到项目 [Langchain-Chatchat](https://github.com/chatchat-space/Langchain-Chatchat) 的启发，实现了一个碎片化信息高效检索的方案。

项目使用 SQLite 作为轻量数据库进行文档和用户的管理，使用了 Langchain.FAISS 提供的高效接口。项目提供大量接口，部署轻便，可对接 企业微信、以及H5下各应用。

### 快速上手

#### 1. 环境配置

- 推荐使用 Python 3.9.16 版本。
  
```shell
# 拉取仓库
$ git clone https://github.com/PluginsKers/KnowledgeBase.git

# 进入目录
$ cd KnowledgeBase

# 安装依赖
$ pip install -r requirements.txt

# 默认依赖包括基本运行环境（FAISS向量库）。
```

#### 2.模型下载

以本项目中默认使用的大语言模型 [THUDM/ChatGLM3-6B](https://huggingface.co/THUDM/chatglm3-6b) 与 Embedding 模型 [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3) 为例：

下载模型需要先[安装 Git LFS](https://docs.github.com/zh/repositories/working-with-files/managing-large-files/installing-git-large-file-storage) ，然后运行

```shell
$ git lfs install
$ git clone https://huggingface.co/THUDM/chatglm3-6b
$ git clone https://huggingface.co/BAAI/bge-m3
$ git clone https://huggingface.co/BAAI/bge-reranker-large
```

#### 3.初始化知识库和配置文件

将项目 src/ 下的 **config.py.template** 改名为 **config.py** 并且按照要求完善配置信息。

注意：本项目只有这一个配置文件。

#### 4.启动项目程序

在项目下运行：

```shell
$ python main.py
```

#### 5.注意事项

项目默认使用 GPU 加速
 