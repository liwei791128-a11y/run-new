import paramiko
import datetime
import time
import socket


def backup_switch_config(hostname, port, username, password):
    """
    备份单个交换机配置
    
    参数:
    - hostname: 交换机IP地址
    - port: SSH端口
    - username: SSH用户名
    - password: SSH密码
    
    返回:
    - (bool, str): 成功状态和结果信息
    """
    # 创建SSH客户端对象
    client = paramiko.SSHClient()
    
    # 自动添加远程服务器的RSA密钥（避免第一次连接时的确认提示）
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # 连接交换机，设置连接超时和欢迎信息超时
        client.connect(hostname=hostname, port=port, 
                      username=username, password=password, 
                      timeout=15, banner_timeout=15)
        
        # 执行备份命令，设置命令执行超时
        stdin, stdout, stderr = client.exec_command('display current-configuration', timeout=30)
        
        # 等待命令执行完成并获取退出状态
        exit_status = stdout.channel.recv_exit_status()
        
        # 检查命令是否执行成功（0表示成功）
        if exit_status != 0:
            error = stderr.read()
            print(f"交换机 {hostname}:{port} 命令执行失败，退出码: {exit_status}, 错误: {error}")
            return False, f"命令执行失败: {error}"
        
        # 读取命令输出的原始字节数据
        output_bytes = stdout.read()
        
        # 尝试不同的编码方式解码，适应不同品牌交换机的编码
        encodings_to_try = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'ascii']
        output = None
        
        for encoding in encodings_to_try:
            try:
                # 尝试用当前编码解码字节数据
                output = output_bytes.decode(encoding)
                print(f"使用编码: {encoding}")
                break
            except UnicodeDecodeError:
                # 如果当前编码解码失败，尝试下一个
                continue
        
        if output is None:
            # 如果所有编码都失败，使用ignore错误处理（忽略无法解码的字符）
            output = output_bytes.decode('utf-8', errors='ignore')
            print(f"警告: 使用ignore模式解码,可能丢失部分字符")
        
        # 获取当前日期时间并格式化为字符串
        current_time = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        
        # 创建包含IP和日期的文件名
        filename = f"{hostname}_{current_time}.txt"
        
        # 将配置保存到本地文件，使用utf-8编码确保跨平台兼容性
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(output)
        
        print(f"交换机 {hostname}:{port} 备份成功！文件已保存为: {filename}")
        return True, filename  # 返回成功状态和文件名
    
    except paramiko.AuthenticationException as e:
        # 处理认证失败的情况
        print(f"交换机 {hostname}:{port} 认证失败，请检查用户名/密码: {e}")
        return False, f"认证失败: {e}"
    
    except paramiko.ssh_exception.NoValidConnectionsError as e:
        # 处理无法连接的情况
        print(f"交换机 {hostname}:{port} 无法连接,请检查IP/端口: {e}")
        return False, f"连接失败: {e}"
    
    except socket.timeout as e:
        # 处理连接或命令执行超时的情况
        print(f"交换机 {hostname}:{port} 连接或命令执行超时: {e}")
        return False, f"连接超时: {e}"
    
    except Exception as e:
        # 处理其他未知异常
        print(f"交换机 {hostname}:{port} 备份失败：{e}")
        return False, f"备份失败: {e}"
    
    finally:
        # 无论成功还是失败，都确保关闭SSH连接
        try:
            client.close()
        except:
            pass


def backup_multiple_switches(switch_list):
    """
    批量备份多台交换机配置
    
    参数:
    switch_list: 交换机信息列表，每个元素是包含以下键的字典:
        - hostname: 交换机IP地址
        - port: SSH端口,默认22
        - username: 用户名
        - password: 密码
    
    返回:
    - (int, int): 成功备份数量和失败备份数量
    """
    print(f"开始备份 {len(switch_list)} 台交换机配置...")
    
    # 初始化成功和失败计数器
    successful_backups = 0
    failed_backups = 0
    
    # 遍历所有交换机
    for i, switch in enumerate(switch_list, 1):
        # 从字典中获取交换机参数，使用默认值处理缺失项
        hostname = switch.get('hostname')
        port = switch.get('port', 22)  # 默认端口22
        username = switch.get('username')
        password = switch.get('password')
        
        # 显示当前备份进度
        print(f"\n[{i}/{len(switch_list)}] 正在备份交换机 {hostname}...")
        
        # 调用单台交换机备份函数
        success, result = backup_switch_config(hostname, port, username, password)
        
        # 根据返回结果更新计数器
        if success:
            successful_backups += 1
        else:
            failed_backups += 1
    
    # 打印备份汇总信息
    print(f"\n{'='*30}")
    print(f"备份完成！")
    print(f"成功: {successful_backups} 台")
    print(f"失败: {failed_backups} 台")
    print(f"{'='*30}")
    
    return successful_backups, failed_backups


# 主程序入口
if __name__ == "__main__":
    """
    主程序入口
    当直接运行此脚本时执行以下代码
    如果被其他模块导入，则不会执行
    """
    # 定义要备份的交换机列表
    switches = [
        {
            'hostname': 'IP',
            'port': 22,
            'username': 'username',
            'password': 'password'
        },
        # 可以继续添加更多交换机
    ]
    
    # 调用批量备份函数
    backup_multiple_switches(switches)