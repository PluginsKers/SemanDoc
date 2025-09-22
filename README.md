![SemanDoc](/assets/SemanDoc.png)

# SemanDoc

SemanDoc 是一个基于语义搜索的文档管理系统，它使用向量数据库和先进的自然语言处理技术来存储、检索和管理文档。

项目主打轻量易用，无需复杂的配置和繁重的依赖，开箱即用，让您可以快速搭建属于自己的文档语义搜索服务。

## 主要特性

- 语义搜索：使用向量嵌入技术实现基于语义的文档搜索
- 文档管理：支持文档的创建、更新、删除和批量操作
- 元数据：支持为文档添加标签和分类
- Webhook 接口：提供轻量级接口，支持从外部系统快速创建文档

## 安装

SemanDoc 基于 `transformers` 库进行语义处理，并使用 `faiss` 实现高效的向量搜索。

1. **克隆代码仓库**
   ```bash
   git clone https://github.com/PluginsKers/SemanDoc.git
   cd SemanDoc
   ```

2. **安装依赖**
   项目所需的所有依赖都已在 `requirements.txt` 文件中列出，可通过 `pip` 命令一键安装。
   ```bash
   pip install -r requirements.txt
   ```
   *注意：`requirements.txt` 中默认使用 `faiss-cpu` 版本。如需 GPU 支持，请自行安装 `faiss-gpu`。*

3. **下载模型**
   项目默认使用 `m3e-large` 模型作为嵌入器。请从 Hugging Face 下载模型文件，并将其放置在 `./models/embedders/` 目录下。

## 运行

使用 `python` 直接运行 `app.py` 即可启动服务。

```bash
python app.py
```

服务启动后，API 将默认在 `http://0.0.0.0:8000` 上监听。

**可选参数:**
- `--host`：指定服务监听的主机地址 (默认为 `0.0.0.0`)。
- `--port`：指定服务监听的端口 (默认为 `8000`)。
- `--save-interval`：设置向量数据库的自动保存间隔（单位：秒），默认为 `300`。

例如，在 `8080` 端口上启动服务：
```bash
python app.py --port 8080
```

## Webhook 功能

系统提供了 webhook 接口，允许外部系统通过简单的 HTTP GET 请求快速创建文档：

```bash
curl -X GET "http://localhost:8000/documents/webhook" \
     -H "Content-Type: application/json" \
     -d '{"content": "文档内容", "tags": ["标签1", "标签2"], "categories": ["分类1"]}'
```