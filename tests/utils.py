import json
import yaml


def _load_test_data(filename):
    """
        Returns:
            次のようなdict
            {
                'request': {...},
                'response': {...}
            }
    """
    try:
        with open(f'tests/cassettes/{filename}') as f:
            data = yaml.load(f)
            return data['interactions'][0]
    except FileNotFoundError:
        # 初回はないため
        return None

def get_response_body_test_data(filename):
    """ レスポンスのbodyを取得 """
    data = _load_test_data(filename)
    if data:
        body_str = data['response']['body']['string']
        return json.loads(body_str)
    else:
        return None
