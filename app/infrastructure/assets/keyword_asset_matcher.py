import unicodedata

from app.domain.models.asset import Asset, AssetQuery


def _fold(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text.lower())
    folded = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    return folded.replace("đ", "d")


class KeywordAssetMatcher:
    """Ranks local asset metadata using explicit suggestions, intent, and keywords."""

    def match(self, query: AssetQuery, assets: list[Asset]) -> list[str]:
        suggested = set(query.suggested_asset_ids)
        folded_message = _fold(query.message)
        ranked: list[tuple[int, str]] = []

        for asset in assets:
            score = 0
            if asset.asset_id in suggested:
                score += 100
            if set(query.intents).intersection(asset.intents):
                score += 20
            score += sum(1 for keyword in asset.keywords if _fold(keyword) in folded_message)
            if score > 0:
                if query.material_code and query.material_code in asset.materials:
                    score += 5
                ranked.append((score, asset.asset_id))

        ranked.sort(key=lambda item: (-item[0], item[1]))
        return [asset_id for _score, asset_id in ranked]
