![SemanDoc](/assets/SemanDoc.png)

# SemanDoc

SemanDoc 是一个基于语义搜索的文档管理系统，它使用向量数据库和先进的自然语言处理技术来存储、检索和管理文档。

## 主要特性

- 语义搜索：使用向量嵌入技术实现基于语义的文档搜索
- 文档管理：支持文档的创建、更新、删除和批量操作
- 元数据管理：支持为文档添加标签和分类
- 相似度检测：自动检测并防止重复文档的添加
- 高性能：支持 GPU 加速，提供高效的文档检索能力
- Webhook 接口：提供轻量级接口，支持从外部系统快速创建文档

## Webhook 功能

系统提供了 webhook 接口，允许外部系统通过简单的 HTTP GET 请求快速创建文档：

```bash
curl -X GET "http://localhost:8000/documents/webhook" \
     -H "Content-Type: application/json" \
     -d '{"content": "文档内容", "tags": ["标签1", "标签2"], "categories": ["分类1"]}'
```
