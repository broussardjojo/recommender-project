from typing import Callable, List

import pandas as pd
import encoding
import featurizing

from sklearn.metrics.pairwise import cosine_similarity


async def get_k_closest_songs(playlist_uri: str,
                        training_data: pd.DataFrame,
                        training_transformers: dict,
                        k: int = 15,
                        comparison: Callable = cosine_similarity) -> List[str]:
    """
    Returns a list of the URIs of the k closest songs found in the dataset.
    :param playlist_uri:
    :param training_data:
    :param training_transformers:
    :param k:
    :param comparison:
    :return:
    """
    training_data_to_use = training_data.drop(columns=encoding.UNUSED_COLUMNS)

    given_auth_args = featurizing.auth_args()
    playlist_feature_vector = await featurizing.get_playlist_vector_from_uri(*given_auth_args, playlist_uri, training_transformers)
    training_data_to_use['similarity'] = comparison(playlist_feature_vector.values.reshape(1, -1),
                                                    training_data_to_use[training_data_to_use.columns]).transpose()
    training_data_to_use = training_data_to_use.sort_values(by='similarity', ascending=False)
    print(training_data_to_use.head(k))
    return list(training_data_to_use.head(k).index)

