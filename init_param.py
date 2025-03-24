def get_init_param():
    return {
        "capabilities": {
            "general": {
                "markdown": {
                    "parser": "marked",
                    "version": "1.1.0"
                },
                "positionEncodings": [
                    "utf-16"
                ],
                "regularExpressions": {
                    "engine": "ECMAScript",
                    "version": "ES2020"
                },
                "staleRequestSupport": {
                    "cancel": True,
                    "retryOnContentModified": [
                        "textDocument/semanticTokens/full",
                        "textDocument/semanticTokens/range",
                        "textDocument/semanticTokens/full/delta"
                    ]
                }
            },
            "notebookDocument": {
                "synchronization": {
                    "dynamicRegistration": True,
                    "executionSummarySupport": True
                }
            },
            "textDocument": {
                "callHierarchy": {
                    "dynamicRegistration": True
                },
                "codeAction": {
                    "codeActionLiteralSupport": {
                        "codeActionKind": {
                            "valueSet": [
                                "",
                                "quickfix",
                                "refactor",
                                "refactor.extract",
                                "refactor.inline",
                                "refactor.rewrite",
                                "source",
                                "source.organizeImports"
                            ]
                        }
                    },
                    "dataSupport": True,
                    "disabledSupport": True,
                    "dynamicRegistration": True,
                    "honorsChangeAnnotations": False,
                    "isPreferredSupport": True,
                    "resolveSupport": {
                        "properties": [
                            "edit"
                        ]
                    }
                },
                "codeLens": {
                    "dynamicRegistration": True
                },
                "colorProvider": {
                    "dynamicRegistration": True
                },
                "completion": {
                    "completionItem": {
                        "commitCharactersSupport": True,
                        "deprecatedSupport": True,
                        "documentationFormat": [
                            "markdown",
                            "plaintext"
                        ],
                        "insertReplaceSupport": True,
                        "insertTextModeSupport": {
                            "valueSet": [
                                1,
                                2
                            ]
                        },
                        "labelDetailsSupport": True,
                        "preselectSupport": True,
                        "resolveSupport": {
                            "properties": [
                                "documentation",
                                "detail",
                                "additionalTextEdits"
                            ]
                        },
                        "snippetSupport": True,
                        "tagSupport": {
                            "valueSet": [
                                1
                            ]
                        }
                    },
                    "completionItemKind": {
                        "valueSet": [
                            1,
                            2,
                            3,
                            4,
                            5,
                            6,
                            7,
                            8,
                            9,
                            10,
                            11,
                            12,
                            13,
                            14,
                            15,
                            16,
                            17,
                            18,
                            19,
                            20,
                            21,
                            22,
                            23,
                            24,
                            25
                        ]
                    },
                    "completionList": {
                        "itemDefaults": [
                            "commitCharacters",
                            "editRange",
                            "insertTextFormat",
                            "insertTextMode"
                        ]
                    },
                    "contextSupport": True,
                    "dynamicRegistration": True,
                    "editsNearCursor": True,
                    "insertTextMode": 2
                },
                "declaration": {
                    "dynamicRegistration": True,
                    "linkSupport": True
                },
                "definition": {
                    "dynamicRegistration": True,
                    "linkSupport": True
                },
                "diagnostic": {
                    "dynamicRegistration": True,
                    "relatedDocumentSupport": False
                },
                "documentHighlight": {
                    "dynamicRegistration": True
                },
                "documentLink": {
                    "dynamicRegistration": True,
                    "tooltipSupport": True
                },
                "documentSymbol": {
                    "dynamicRegistration": True,
                    "hierarchicalDocumentSymbolSupport": True,
                    "labelSupport": True,
                    "symbolKind": {
                        "valueSet": [
                            1,
                            2,
                            3,
                            4,
                            5,
                            6,
                            7,
                            8,
                            9,
                            10,
                            11,
                            12,
                            13,
                            14,
                            15,
                            16,
                            17,
                            18,
                            19,
                            20,
                            21,
                            22,
                            23,
                            24,
                            25,
                            26
                        ]
                    },
                    "tagSupport": {
                        "valueSet": [
                            1
                        ]
                    }
                },
                "foldingRange": {
                    "dynamicRegistration": True,
                    "foldingRange": {
                        "collapsedText": False
                    },
                    "foldingRangeKind": {
                        "valueSet": [
                            "comment",
                            "imports",
                            "region"
                        ]
                    },
                    "lineFoldingOnly": True,
                    "rangeLimit": 5000
                },
                "formatting": {
                    "dynamicRegistration": True
                },
                "hover": {
                    "contentFormat": [
                        "markdown",
                        "plaintext"
                    ],
                    "dynamicRegistration": True
                },
                "implementation": {
                    "dynamicRegistration": True,
                    "linkSupport": True
                },
                "inactiveRegionsCapabilities": {
                    "inactiveRegions": True
                },
                "inlayHint": {
                    "dynamicRegistration": True,
                    "resolveSupport": {
                        "properties": [
                            "tooltip",
                            "textEdits",
                            "label.tooltip",
                            "label.location",
                            "label.command"
                        ]
                    }
                },
                "inlineValue": {
                    "dynamicRegistration": True
                },
                "linkedEditingRange": {
                    "dynamicRegistration": True
                },
                "onTypeFormatting": {
                    "dynamicRegistration": True
                },
                "publishDiagnostics": {
                    "codeDescriptionSupport": True,
                    "dataSupport": True,
                    "relatedInformation": True,
                    "tagSupport": {
                        "valueSet": [
                            1,
                            2
                        ]
                    },
                    "versionSupport": False
                },
                "rangeFormatting": {
                    "dynamicRegistration": True
                },
                "references": {
                    "dynamicRegistration": True
                },
                "rename": {
                    "dynamicRegistration": True,
                    "honorsChangeAnnotations": True,
                    "prepareSupport": True,
                    "prepareSupportDefaultBehavior": 1
                },
                "selectionRange": {
                    "dynamicRegistration": True
                },
                "semanticTokens": {
                    "augmentsSyntaxTokens": True,
                    "dynamicRegistration": True,
                    "formats": [
                        "relative"
                    ],
                    "multilineTokenSupport": False,
                    "overlappingTokenSupport": False,
                    "requests": {
                        "full": {
                            "delta": True
                        },
                        "range": True
                    },
                    "serverCancelSupport": True,
                    "tokenModifiers": [
                        "declaration",
                        "definition",
                        "readonly",
                        "static",
                        "deprecated",
                        "abstract",
                        "async",
                        "modification",
                        "documentation",
                        "defaultLibrary"
                    ],
                    "tokenTypes": [
                        "namespace",
                        "type",
                        "class",
                        "enum",
                        "interface",
                        "struct",
                        "typeParameter",
                        "parameter",
                        "variable",
                        "property",
                        "enumMember",
                        "event",
                        "function",
                        "method",
                        "macro",
                        "keyword",
                        "modifier",
                        "comment",
                        "string",
                        "number",
                        "regexp",
                        "operator",
                        "decorator"
                    ]
                },
                "signatureHelp": {
                    "contextSupport": True,
                    "dynamicRegistration": True,
                    "signatureInformation": {
                        "activeParameterSupport": True,
                        "documentationFormat": [
                            "markdown",
                            "plaintext"
                        ],
                        "parameterInformation": {
                            "labelOffsetSupport": True
                        }
                    }
                },
                "synchronization": {
                    "didSave": True,
                    "dynamicRegistration": True,
                    "willSave": True,
                    "willSaveWaitUntil": True
                },
                "typeDefinition": {
                    "dynamicRegistration": True,
                    "linkSupport": True
                },
                "typeHierarchy": {
                    "dynamicRegistration": True
                }
            },
            "window": {
                "showDocument": {
                    "support": True
                },
                "showMessage": {
                    "messageActionItem": {
                        "additionalPropertiesSupport": True
                    }
                },
                "workDoneProgress": True
            },
            "workspace": {
                "applyEdit": True,
                "codeLens": {
                    "refreshSupport": True
                },
                "configuration": True,
                "diagnostics": {
                    "refreshSupport": True
                },
                "didChangeConfiguration": {
                    "dynamicRegistration": True
                },
                "didChangeWatchedFiles": {
                    "dynamicRegistration": True,
                    "relativePatternSupport": True
                },
                "executeCommand": {
                    "dynamicRegistration": True
                },
                "fileOperations": {
                    "didCreate": True,
                    "didDelete": True,
                    "didRename": True,
                    "dynamicRegistration": True,
                    "willCreate": True,
                    "willDelete": True,
                    "willRename": True
                },
                "inlayHint": {
                    "refreshSupport": True
                },
                "inlineValue": {
                    "refreshSupport": True
                },
                "semanticTokens": {
                    "refreshSupport": True
                },
                "symbol": {
                    "dynamicRegistration": True,
                    "resolveSupport": {
                        "properties": [
                            "location.range"
                        ]
                    },
                    "symbolKind": {
                        "valueSet": [
                            1,
                            2,
                            3,
                            4,
                            5,
                            6,
                            7,
                            8,
                            9,
                            10,
                            11,
                            12,
                            13,
                            14,
                            15,
                            16,
                            17,
                            18,
                            19,
                            20,
                            21,
                            22,
                            23,
                            24,
                            25,
                            26
                        ]
                    },
                    "tagSupport": {
                        "valueSet": [
                            1
                        ]
                    }
                },
                "workspaceEdit": {
                    "changeAnnotationSupport": {
                        "groupsOnLabel": True
                    },
                    "documentChanges": True,
                    "failureHandling": "textOnlyTransactional",
                    "normalizesLineEndings": True,
                    "resourceOperations": [
                        "create",
                        "rename",
                        "delete"
                    ]
                },
                "workspaceFolders": True
            }
        },
        "clientInfo": {
            "name": "Visual Studio Code",
            "version": "1.98.2"
        },
        "initializationOptions": {
            "clangdFileStatus": True,
            "fallbackFlags": []
        },
        "locale": "zh-cn",
        # "processId": 6156,
        "rootPath": "d:\\proj\\STM32F10x-MesonBuild-Demo",
        "rootUri": "file:///d%3A/proj/STM32F10x-MesonBuild-Demo",
        "trace": "off",
        "workspaceFolders": [
            {
                "name": "STM32F10x-MesonBuild-Demo",
                "uri": "file:///d%3A/proj/STM32F10x-MesonBuild-Demo"
            }
        ]
    }
