import configparser
import io

from qcloud_cos import CosConfig, CosClientError
from qcloud_cos import CosS3Client
from PIL import Image

class CosService:

    def __init__(self, config: configparser.ConfigParser, connection_section='connection'):
        self.config = config

        self.secret_id = config.get(connection_section, 'access_key_id')
        self.secret_key = config.get(connection_section, 'access_key_secret')
        self.endpoint = config.get(connection_section, 'endpoint')
        self.region = None  # 通过 Endpoint 初始化不需要配置 region
        self.token = None  # 如果使用永久密钥不需要填入 token，如果使用临时密钥需要填入
        self.scheme = 'https'  # 指定使用 http/https 协议来访问 COS，默认为 https，可不填

        self.config = CosConfig(Region=self.region,
                                SecretId=self.secret_id,
                                SecretKey=self.secret_key,
                                Token=self.token,
                                Endpoint=self.endpoint,
                                Scheme=self.scheme)

        self.client = CosS3Client(self.config)

    def get_value(self, section, option):
        return self.config.get(section, option)

    def upload_file_to_oss(self, local_file_path: str, bucket_name: str, key: str, retry=3) -> str:

        for i in range(retry):
            try:
                response = self.client.upload_file(
                    Bucket=bucket_name,
                    LocalFilePath=local_file_path,
                    Key=key,
                    PartSize=5,
                    MAXThread=10,
                    EnableMD5=False)
                return response
            except CosClientError as e:
                if i >= retry - 1:
                    raise e

    def upload_object_to_oss(self, data, bucket_name: str, key: str) -> str:
        if isinstance(data, Image.Image):
            img_byte_arr = io.BytesIO()
            # image.save expects a file-like as a argument
            data.save(img_byte_arr, format='png')
            # Turn the BytesIO object back into a bytes object
            data = img_byte_arr.getvalue()

        response = self.client.put_object(
            Bucket=bucket_name,
            Body=data,
            Key=key,
            StorageClass='STANDARD',
            EnableMD5=False)

        return response
