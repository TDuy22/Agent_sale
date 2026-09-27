from app.domain.models.asset import Asset, AssetQuery
from app.infrastructure.text import fold


class KeywordAssetMatcher:
    """Ranks assets by flow suggestion, then intent, then keywords in the message."""

    SUGGESTED_SCORE = 100
    INTENT_SCORE = 20
    MATERIAL_BONUS = 5

    def match(self, query: AssetQuery, assets: list[Asset]) -> list[Asset]:
        suggested = set(query.suggested_asset_ids)
        folded_message = fold(query.message)
        ranked: list[tuple[int, Asset]] = []

        for asset in assets:
            score = 0
            if asset.asset_id in suggested:
                score += self.SUGGESTED_SCORE
            if set(query.intents).intersection(asset.intents):
                score += self.INTENT_SCORE
            score += sum(1 for keyword in asset.keywords if fold(keyword) in folded_message)
            if score > 0:
                if query.material_code and query.material_code in asset.materials:
                    score += self.MATERIAL_BONUS
                ranked.append((score, asset))

        ranked.sort(key=lambda item: (-item[0], item[1].asset_id))
        return [asset for _score, asset in ranked]
