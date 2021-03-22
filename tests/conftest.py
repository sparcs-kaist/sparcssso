from rest_framework.test import APIClient


class RequestSettingMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_client = APIClient()

    def http_request(self, user, method, path, data=None, querystring='', **kwargs):
        self.api_client.force_authenticate(user=user)

        request_func = {
            'post': self.api_client.post,
            'patch': self.api_client.patch,
            'put': self.api_client.put,
            'get': self.api_client.get,
            'delete': self.api_client.delete
        }
        url = f'/{path}/?{querystring}'
        return request_func[method](url, data=data, format='json', **kwargs)
