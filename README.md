# Kubernetes 系统化教学手册

> 一份系统化的 Kubernetes 学习材料：从容器原理、集群架构，到网络、存储、调度、可观测性与生产实践。初学者先完成入门实验，再按需深入原理；涉及版本、插件和生产操作的内容应结合对应官方文档核对。

**第一次学习？** 从 [小白入门实验](./BEGINNER_GUIDE.md) 开始，配套 [完整实验清单](./examples/beginner/app.yaml)。本次核查的订正、官方依据、验证边界与优化建议见 [内容核查报告](./CONTENT_REVIEW.md)。

**Apple silicon Mac 用户：** 从 [Apple container 实验指南](./APPLE_CONTAINER_GUIDE.md) 开始，用原生容器构建、访问和调试网站，再把同一镜像导入独立 Kubernetes 集群。43 章均有对应实验入口，网页附录 E 完整收录指南，可离线阅读。原生命令基于已实测的 container 1.0.0；Kubernetes、插件与多节点实验分别标注前提。

[![Single File](https://img.shields.io/badge/单文件-HTML-blue)](./index.html)
[![Offline](https://img.shields.io/badge/离线-零依赖-green)](./index.html)
[![Chapters](https://img.shields.io/badge/章节-43-orange)](./index.html)

---

## 这是什么

这不是一份速查表，也不是一篇综述，而是**一条被设计好的学习路径**。

Kubernetes 的学习难点从来不在「某个命令怎么用」，而在于**概念之间的依赖关系**。很多人在没有理解 Linux 容器隔离机制的情况下直接去背 Pod、Service、Deployment 的定义，结果是能跑通教程，却无法解释「为什么 Pod 里的容器共享网络命名空间」「为什么 Service 需要一个不存在的虚拟 IP」这类问题。一旦生产环境出问题，这种理解深度的差距就会暴露出来。

因此本手册采取**自底向上、逐层递进**的组织方式。每一章都建立在前一章已经建立的概念之上，并在需要时明确回顾前置知识。

---

## 内容概览

全书共 **43 章 + 5 个附录**，分为九篇：

| 篇 | 主题 | 回答的核心问题 |
|---|---|---|
| 第一篇 | 容器技术基础 | 容器到底是什么？它凭什么比虚拟机轻？镜像为什么能分层复用？ |
| 第二篇 | Kubernetes 架构 | 单个容器能跑起来，但成千上万个怎么办？谁来做决策？ |
| 第三篇 | 网络 | Pod 之间如何通信？一个虚拟 IP 如何把流量送到真实容器？ |
| 第四篇 | 存储 | 容器随时可能被销毁，数据往哪里放？ |
| 第五篇 | 配置与安全 | 配置怎么注入？谁有权限做什么？如何防止容器逃逸？ |
| 第六篇 | 调度与资源 | Pod 被放到哪台机器上？资源如何分配与隔离？如何自动扩缩？ |
| 第七篇 | 可观测性 | 系统运行起来后，如何知道它是否健康、哪里慢？ |
| 第八篇 | 生产化实践 | 如何规划集群、安全升级、治理多租户、控制成本、排查故障？ |
| 第九篇 | 服务网格与扩展 | 微服务间的流量治理如何做？如何扩展 Kubernetes 本身？ |

### 章节清单

<details>
<summary><b>展开查看全部 43 章</b></summary>

**导论**

0· 如何使用本手册

**第一篇　容器技术基础**

1. 隔离与虚拟化原理
2. Namespace 与 Cgroups
3. 容器镜像与分层文件系统
4. Docker 架构与核心操作
5. Dockerfile 与镜像构建
6. 容器网络与存储基础
7. 从 Docker 到 OCI 与 CRI

**第二篇　Kubernetes 架构**

8. 编排问题的本质
9. 集群架构与核心组件
10. 声明式 API 与控制器模式
11. Pod 深入剖析
12. 工作负载控制器
13. Service 与服务发现
14. 命名空间 / 标签 / 注解

**第三篇　网络**

15. Kubernetes 网络模型
16. CNI 与主流实现
17. Service 转发实现原理
18. 集群 DNS
19. Ingress 与 Gateway API
20. NetworkPolicy 网络策略

**第四篇　存储**

21. Volume 体系
22. PV / PVC / StorageClass
23. CSI 与有状态存储

**第五篇　配置与安全**

24. ConfigMap 与 Secret
25. 认证、授权与 RBAC
26. Pod 安全与运行时隔离

**第六篇　调度与资源**

27. 调度器工作原理
28. 资源请求、限制与 QoS
29. 亲和性、污点与拓扑分布
30. 优先级、抢占与中断预算
31. 自动扩缩容

**第七篇　可观测性**

32. 可观测性体系与性能方法论
33. 指标、日志与链路追踪
34. eBPF 无侵入观测

**第八篇　生产化实践**

35. 集群规划与高可用
36. 版本升级与变更管理
37. 多租户与资源治理
38. 成本优化
39. 故障排查手册

**第九篇　服务网格与扩展**

40. 服务网格原理与 Istio
41. Istio 流量管理与安全
42. Ambient 无侧车模式
43. CRD、Operator 与准入控制

**附录**

- A · kubectl 命令速查
- B · YAML 模板库
- C · 术语表
- D · 学习路径与自测题
- E · Apple container 全章节实验路线

</details>

---

## 阅读路径

| 路径 | 说明 |
|---|---|
| **小白入门**（推荐初学者） | 先完成入门实验，再读第 8–13、24、28、39 章的基础段落，建立部署与排障能力。 |
| **Apple container 实验**（Apple silicon Mac） | 先做 E00–E07 原生容器，再做 E08 镜像流转与 Kubernetes；每章实验给出任务、命令、验收和环境边界。 |
| **系统深入学习** | 从第 1 章顺序读到第 43 章。适合已有实践基础、希望理解原理或承担平台建设职责的读者。 |
| **运维速成** | 先读第 2、8、9、11、12、39 章，快速建立可用认知并掌握排障方法，再按需回补网络、存储、调度各篇。 |
| **按需查阅** | 利用左侧导航直接跳转。每章开头的「本章要点」和结尾的「小结」可以帮助快速定位。术语不确定时查附录 C。 |

---

## 使用方式

**方式一：本地打开**

直接用浏览器打开 `index.html` 即可，无需任何服务器或网络连接。

```bash
# macOS
open index.html

# Linux
xdg-open index.html

# Windows
start index.html
```

**方式二：在线访问**

本仓库根文件为 `index.html`，可直接启用 GitHub Pages 在线阅读：

`Settings → Pages → Source 选择 main 分支根目录` → 访问 `https://baokaijian.github.io/learnk8s/`

---

## 技术特性

- **单文件交付** —— 全部内容、样式、脚本内联于一个 HTML 文件，体积约 1.2 MB，便于分发、归档与离线阅读。
- **零外部加载依赖** —— 正文、样式和脚本内联，不加载外部字体、CDN 或图片，断网可阅读。官方参考链接需联网访问，实验安装与镜像下载也需相应网络。
- **清晰的学习入口** —— 首屏可选择小白入门、Apple container 实验或原理学习，实验卡先展示任务，展开后查看准备环境、命令、结果与适用范围。
- **深色主题排版** —— 正文行宽、文字对比度与层级适合持续阅读；代码块、表格、提示框分别排版。
- **侧边栏导航 + 章节内容搜索** —— 匹配章节标题和正文关键词，显示结果数与空结果提示；不提供句子级结果或命中位置高亮。
- **阅读进度条与回到顶部** —— 长文档阅读体验优化。
- **手机与平板阅读** —— 固定导航显示当前章节，目录支持触控、键盘和关闭后恢复焦点；平板使用双列入口，手机使用单列。宽表格、代码和图示可单独横向滑动，溢出时显示提示。
- **实验命令复制** —— Apple 实验提供复制按钮；浏览器限制剪贴板时会选中代码供系统复制。支持减少动态效果的系统偏好。

---

## 目录结构

```
learnk8s/
├── index.html                   # 主体（43 章 + 导论 + 5 附录）
├── README.md                    # 本文件
├── BEGINNER_GUIDE.md            # 入门实验、预期结果与排障路径
├── APPLE_CONTAINER_GUIDE.md     # Apple 原生实验与 Kubernetes 衔接
├── CONTENT_REVIEW.md            # 内容订正、官方依据与优化建议
├── examples/beginner/app.yaml   # 完整的标准资源实验清单
├── examples/apple-container/   # 网站镜像、43 章任务及配置/存储/RBAC/策略/HPA/配额清单
├── scripts/validate_content.py  # YAML 与可选 OpenAPI 静态核查
├── scripts/sync_apple_labs.py   # 将 Apple 指南和各章任务同步到离线 HTML
└── .gitignore                   # 忽略本地工作目录数据
```

---

## 维护实验内容

Apple 指南与 43 章任务分别维护在 `APPLE_CONTAINER_GUIDE.md`、`examples/apple-container/chapter-labs.json`。修改后同步网页并检查：

```bash
python3 scripts/sync_apple_labs.py
python3 scripts/sync_apple_labs.py --check
python3 scripts/validate_content.py
```

同步脚本仅用 Python 标准库；YAML 检查需要 PyYAML。它们不连接集群。Apple 原生实验已实际运行，Kubernetes 衔接清单已静态检查；QEMU 集群导入与插件实验尚需按指南在相应环境验收。

---

## 适用读者

- 准备系统学习 Kubernetes、希望建立完整心智模型的开发者
- 承担集群建设与平台工程职责的运维 / SRE 工程师
- 需要一份可离线分发的内部培训材料的团队
- 面试前需要系统性梳理云原生知识体系的求职者

---

## 许可与说明

本手册为教学材料，内容组织与行文均为原创整理。文中涉及的 Kubernetes、Docker、Istio 等名称与商标归各自权利人所有，此处仅作技术讲解之用。
