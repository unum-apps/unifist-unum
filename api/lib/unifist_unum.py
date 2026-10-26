"""
The models Unifist Unum owns
"""

import relations
import relations_unifist
import relations_unum

SOURCES = [relations_unifist.UnifistBase.SOURCE, relations_unum.UnumBase.SOURCE]

def models():
    """
    The six tables everything else uses: Sequence, Slug and Journal from relations-unifist in the unifist
    schema, Route, Scribe and Clash from relations-unum in the unum schema
    """

    return (
        relations.models(relations_unifist, relations_unifist.UnifistBase) +
        relations.models(relations_unum, relations_unum.UnumBase)
    )
