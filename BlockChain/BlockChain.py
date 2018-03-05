"""
本Demo数据结构
block = {
    'index': 1,  区块索引
    'timestamp': 1506057125.900785, 时间戳
    'transactions': [  区块信息(交易列表)
        {
            'sender': "8527147fe1f5426f9dd545de4b27ee00",
            'recipient': "a77f5cdfa2934df3954a5c7c7da5df1f",
            'amount': 5,
        }
    ],
    'proof': 324984774000,  工作量证明
    'previous_hash': "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"  前一区块信息
}
"""
import hashlib
import json
import requests
from time import time
from urllib.parse import urlparse


class BlockChain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        # 创世块初始化
        self.new_block(previous_hash=1, proof=100)
        # 存储节点
        self.nodes = set()

    def new_block(self, proof, previous_hash=None):
        # 创建新的区块并添加到该条链中
        """
        生成新块
        :param proof: <int> 工作算法证明给出的证明
        :param previous_hash: (Optional) <str> 上一个工作块的Hash值
        :return:<dict> 新块
        """
        block = {
            'index': len(self.chain) + 1,
            'timestemp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        # 重置当前事务列表
        self.current_transactions = []
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        # 添加一个新的事务到事务链中
        """
        生成新的交易信息,信息将加入到下一个待挖区块中
        :param sender: <str>发送人的地址
        :param recipient: <str> 接收人的地址
        :param amount: <int> 数量
        :return:<int> 区块的索引,用于保持事务的连续性
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })
        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        # 将一个区块哈希化
        """
        生成块的 SHA-256 hash值
        :param block: <dict> 区块
        :return: <str> 区块Hash值
        """
        # 我们必须确保字典是有序的，否则我们就会有不一致的哈希表
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        # 返回一个链中的随后一个区块
        return self.chain[-1]

    def proof_of_work(self, last_proof):
        """
        简单的工作量证明
            - 查找一个'p' 使得hash(pp')以四个0开头
            - p是上一个块的证明,p'是当前的证明
        :param last_proof:  <int>
        :return: <int
        """
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        验证证明:是否hash(last_proof,proof)以四个0开头?
        :param last_proof: <int> 前一个工作证明
        :param proof: <int> 当前工作证明
        :return: <bool> 是否通过验证
        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    def register_node(self, address):
        """
        新增一个节点到节点列表
        :param address: <str> 节点的列表,例如:'http://192.168.1.1:5000'
        :return: None
        """
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def valid_chain(self, chain):
        """
        裁决一个已验证的区块链
        :param chain: <list> 一个区块链
        :return: <bool> 裁决是否通过
        """
        last_block = chain[0]
        current_index = 1
        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n---------------\n")
            # 检查该区块的hash值是否正确
            if block['previous_hash'] != self.hash(last_block):
                return False
            # 检查工作中的工作量是否正确
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False
            last_block = block
            current_index += 1
        return True

    def resolve_conflicts(self):
        """
        共识算法解决冲突
        使用网络中最长的链
        :return: <bool> 链是否被取代
        """
        neighbours = self.nodes
        new_chain = None
        # 我们只关注比我们长的链
        max_length = len(self.chain)
        # 从我们网络中的所有节点获取并验证链
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                # 检查链长度是否较长和该链是否被验证
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain
        # 将本来的链替换成新的链,校验该链是否比我们自带的链长
        if new_chain:
            self.chain = new_chain
            return True
        return False
