from connectors.rss_connector import RSSConnector
from connectors.newsapi_connector import NewsAPIConnector
from connectors.gnews_connector import GNewsConnector



class ConnectorFactory:


    @staticmethod
    def create(config):

        connector_type = config.get(
            "type"
        )


        if connector_type == "rss":

            return RSSConnector(
                config
            )


        elif connector_type == "newsapi":

            return NewsAPIConnector(
                config
            )


        elif connector_type == "gnews":

            return GNewsConnector(
                config
            )


        else:

            raise ValueError(
                f"Unknown connector type: {connector_type}"
            )