import unittest
import logging
from raptor import RetrievalAugmentation

# 配置日志输出
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class TestRetrievalAugmentation(unittest.TestCase):
    """测试RetrievalAugmentation类的get_all_nodes_info方法"""

    def setUp(self):
        """测试前的准备工作"""
        self.ra = RetrievalAugmentation()

        with open('demo/灰姑娘.txt', 'r', encoding='utf-8') as file:
            self.test_docs = file.read()
        logging.info("测试文档准备完成")

    def test_get_all_nodes_info_without_documents(self):
        """测试在未添加文档时调用get_all_nodes_info"""
        with self.assertRaises(ValueError) as context:
            self.ra.get_all_nodes_info()
        self.assertTrue("树未初始化" in str(context.exception))
        logging.info("未添加文档的测试通过")
        
    def test_get_all_nodes_info_with_documents(self):
        """测试添加文档后调用get_all_nodes_info"""
        # 添加测试文档
        logging.info("开始添加文档...")
        self.ra.add_documents(self.test_docs)
        logging.info("文档添加完成")
        
        # 获取节点信息
        logging.info("获取节点信息...")
        nodes_info = self.ra.get_all_nodes_info()
        logging.info(f"获取到的节点信息: {nodes_info}")
        
        # 验证返回的数据结构
        self.assertIsInstance(nodes_info, dict)
        self.assertIn('leaf_nodes', nodes_info)
        self.assertIn('summary_nodes', nodes_info)
        self.assertIn('num_layers', nodes_info)
        self.assertIn('total_nodes', nodes_info)
        
        # 验证叶子节点
        self.assertIsInstance(nodes_info['leaf_nodes'], list)
        logging.info(f"叶子节点数量: {len(nodes_info['leaf_nodes'])}")
        for node in nodes_info['leaf_nodes']:
            self.assertIn('text', node)
            self.assertIn('index', node)
            self.assertIsInstance(node['text'], str)
            self.assertIsInstance(node['index'], int)
            logging.debug(f"叶子节点内容: {node['text'][:50]}...")
            
        # 验证摘要节点
        self.assertIsInstance(nodes_info['summary_nodes'], dict)
        logging.info(f"摘要节点层数: {len(nodes_info['summary_nodes'])}")
        for layer, nodes in nodes_info['summary_nodes'].items():
            logging.info(f"第 {layer} 层节点数量: {len(nodes)}")
            self.assertIsInstance(layer, int)
            self.assertIsInstance(nodes, list)
            for node in nodes:
                self.assertIn('text', node)
                self.assertIn('index', node)
                self.assertIn('children', node)
                self.assertIsInstance(node['text'], str)
                self.assertIsInstance(node['index'], int)
                self.assertIsInstance(node['children'], list)
                logging.debug(f"摘要节点内容: {node['text'][:50]}...")
                
        # 验证基本信息
        logging.info(f"树的层数: {nodes_info['num_layers']}")
        logging.info(f"总节点数: {nodes_info['total_nodes']}")
        self.assertIsInstance(nodes_info['num_layers'], int)
        self.assertIsInstance(nodes_info['total_nodes'], int)
        self.assertGreater(nodes_info['total_nodes'], 0, "总节点数应该大于0")
        self.assertGreater(nodes_info['num_layers'], 0, "树的层数应该大于0")
        
        # 验证节点关系
        for layer, nodes in nodes_info['summary_nodes'].items():
            for node in nodes:
                logging.debug(f"检查第 {layer} 层节点 {node['index']} 的子节点: {node['children']}")
                # 验证子节点索引是否有效
                for child_index in node['children']:
                    # 子节点索引应该小于总节点数
                    self.assertLess(child_index, nodes_info['total_nodes'])
                    
    def test_get_all_nodes_info_data_consistency(self):
        """测试节点信息的数据一致性"""
        # 添加测试文档
        logging.info("开始添加文档...")
        self.ra.add_documents(self.test_docs)
        logging.info("文档添加完成")
        
        logging.info("获取节点信息...")
        nodes_info = self.ra.get_all_nodes_info()
        logging.info(f"获取到的节点信息: {nodes_info}")
        
        # 验证叶子节点数量
        leaf_count = len(nodes_info['leaf_nodes'])
        logging.info(f"叶子节点数量: {leaf_count}")
        self.assertGreater(leaf_count, 0, "叶子节点数量应该大于0")
        
        # 验证每层节点的数量关系
        for layer in range(nodes_info['num_layers'] - 1):
            if layer in nodes_info['summary_nodes']:
                current_layer_count = len(nodes_info['summary_nodes'][layer])
                logging.info(f"第 {layer} 层节点数量: {current_layer_count}")
                if layer + 1 in nodes_info['summary_nodes']:
                    next_layer_count = len(nodes_info['summary_nodes'][layer + 1])
                    logging.info(f"第 {layer + 1} 层节点数量: {next_layer_count}")
                    # 上层节点数应该小于等于下层节点数
                    self.assertLessEqual(next_layer_count, current_layer_count)

if __name__ == '__main__':
    unittest.main()
