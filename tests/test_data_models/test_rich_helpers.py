from databooks.data_models._rich import HtmlTable
from tests.test_tui import render


def test_html_table() -> None:
    """HTML can be rendered to a `rich` table."""
    html = [
        "<div>\n",
        "<style scoped>\n",
        "    .dataframe tbody tr th:only-of-type {\n",
        "        vertical-align: middle;\n",
        "    }\n",
        "\n",
        "    .dataframe tbody tr th {\n",
        "        vertical-align: top;\n",
        "    }\n",
        "\n",
        "    .dataframe thead th {\n",
        "        text-align: right;\n",
        "    }\n",
        "</style>\n",
        '<table border="1" class="dataframe">\n',
        "  <thead>\n",
        '    <tr style="text-align: right;">\n',
        "      <th></th>\n",
        "      <th>col0</th>\n",
        "      <th>col1</th>\n",
        "      <th>col2</th>\n",
        "    </tr>\n",
        "  </thead>\n",
        "  <tbody>\n",
        "    <tr>\n",
        "      <th>0</th>\n",
        "      <td>0.849474</td>\n",
        "      <td>0.756456</td>\n",
        "      <td>0.268569</td>\n",
        "    </tr>\n",
        "    <tr>\n",
        "      <th>1</th>\n",
        "      <td>0.511937</td>\n",
        "      <td>0.357224</td>\n",
        "      <td>0.570879</td>\n",
        "    </tr>\n",
        "    <tr>\n",
        "      <th>2</th>\n",
        "      <td>0.836116</td>\n",
        "      <td>0.928280</td>\n",
        "      <td>0.946514</td>\n",
        "    </tr>\n",
        "    <tr>\n",
        "      <th>3</th>\n",
        "      <td>0.803129</td>\n",
        "      <td>0.540215</td>\n",
        "      <td>0.335783</td>\n",
        "    </tr>\n",
        "    <tr>\n",
        "      <th>4</th>\n",
        "      <td>0.074853</td>\n",
        "      <td>0.661168</td>\n",
        "      <td>0.344527</td>\n",
        "    </tr>\n",
        "    <tr>\n",
        "      <th>5</th>\n",
        "      <td>0.299696</td>\n",
        "      <td>0.782420</td>\n",
        "      <td>0.970147</td>\n",
        "    </tr>\n",
        "    <tr>\n",
        "      <th>6</th>\n",
        "      <td>0.159906</td>\n",
        "      <td>0.566822</td>\n",
        "      <td>0.243798</td>\n",
        "    </tr>\n",
        "    <tr>\n",
        "      <th>7</th>\n",
        "      <td>0.896461</td>\n",
        "      <td>0.174406</td>\n",
        "      <td>0.758376</td>\n",
        "    </tr>\n",
        "    <tr>\n",
        "      <th>8</th>\n",
        "      <td>0.708324</td>\n",
        "      <td>0.895195</td>\n",
        "      <td>0.769364</td>\n",
        "    </tr>\n",
        "    <tr>\n",
        "      <th>9</th>\n",
        "      <td>0.860726</td>\n",
        "      <td>0.381919</td>\n",
        "      <td>0.329727</td>\n",
        "    </tr>\n",
        "  </tbody>\n",
        "</table>\n",
        "</div>",
    ]
    assert (
        render(HtmlTable("".join(html)).rich())
        == """\
                                      \n\
      col0       col1       col2      \n\
 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ \n\
  0   0.849474   0.756456   0.268569  \n\
  1   0.511937   0.357224   0.570879  \n\
  2   0.836116   0.928280   0.946514  \n\
  3   0.803129   0.540215   0.335783  \n\
  4   0.074853   0.661168   0.344527  \n\
  5   0.299696   0.782420   0.970147  \n\
  6   0.159906   0.566822   0.243798  \n\
  7   0.896461   0.174406   0.758376  \n\
  8   0.708324   0.895195   0.769364  \n\
  9   0.860726   0.381919   0.329727  \n\
                                      \n\
"""
    )
