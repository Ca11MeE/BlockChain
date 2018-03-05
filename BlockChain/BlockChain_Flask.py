from uuid import uuid4

from flask import Flask, jsonify, request

# Instantiate our Node 创建一个节点
from BlockChain import BlockChain

app = Flask(__name__)
# Generate a globally unique address for this node 为节点随机创建一个名字
node_identifier = str(uuid4()).replace('-', '')
# Instantiate the Blockchain  实例化区块链类
blockchain = BlockChain()


@app.route('/mine', methods=['GET'])
def mine():
    # return "We'll mine a new Block"
    # We run the proof of work algorithm to get the next proof...  计算工作量证明
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)
    # 给工作量证明的节点提供奖励.
    # 发送者为 "0" 表明是新挖出的币
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )
    # Forge the new Block by adding it to the chain 添加新的区块用于新增到链中
    block = blockchain.new_block(proof)
    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


# 发送交易数据
@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    # return "We'll add a new transaction"
    #  获取请求体json数据
    values = request.get_json()
    # Check that the required fields are in the POST'ed data  获取post请求的对应数据
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400
    # Create a new Transaction 创建一个新的事务
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])
    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


# 返回整个区块链
@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


# 添加URL形式的新节点列表,用于注册节点
@app.route('/nodes/register', methods=['POST'])
def nodes_register():
    # 获取节点注册信息
    values = request.get_json()
    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400
    for node in nodes:
        blockchain.register_node(node)
    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


# 执行一致性算法,解决任何冲突,确保节点拥有正确的链
@app.route('/nodes/resolve', methods=['GET'])
def nodes_resolve():
    replaced = blockchain.resolve_conflicts()
    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }
    return jsonify(response), 200


# 定义服务器运行环境
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
