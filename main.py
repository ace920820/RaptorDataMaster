import os
os.environ["OPENAI_API_KEY"] = "sk-S9g07d99109588ce7750c3c2f8f7537fd5c4f8e722c1T4qF"

from raptor import RetrievalAugmentation

# Initialize with default configuration. For advanced configurations, check the documentation. [WIP]
RA = RetrievalAugmentation()
with open('demo/灰姑娘.txt', 'r',encoding='utf-8') as file:
    text = file.read()
RA.add_documents(text)

# SAVE_PATH = "demo/cinderella0205"
# RA = RetrievalAugmentation(tree=SAVE_PATH)

# print("获取节点信息...")
# nodes_info = RA.get_all_nodes_info()
# print(f"获取到的节点信息: {nodes_info}")

question = "灰姑娘是如何获得的幸福"
answer = RA.answer_question(question=question)
print("Answer: ", answer)

SAVE_PATH = "demo/cinderella0205"
RA.save(SAVE_PATH)