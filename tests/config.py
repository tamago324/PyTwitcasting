import os

import vcr


TOKEN = os.environ['ACCESS_TOKEN']

# URLとリクエストメソッドが一致するリクエストが同一とみなされる
tape = vcr.VCR(
    # JSONだとバイナリを保存できないため(デフォルトでyamlだけど明示しておく
    serializer='yaml',
    cassette_library_dir='tests/cassettes',
    record_mode='once',
    # アクセストークンを消去する
    filter_headers=['Authorization'],
    # テスト関数名を使い、自動生成
    path_transformer=vcr.VCR.ensure_suffix('.yaml')
)
