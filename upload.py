import cohere
import os
import hnswlib
from typing import List, Dict
from unstructured.partition.auto import partition
from unstructured.chunking.title import chunk_by_title


from dotenv import load_dotenv
load_dotenv()

COHERE_API_KEY = os.environ["COHERE_API_KEY"]

co = cohere.Client(COHERE_API_KEY)



class Loader:

    def __init__(self, path):
        self.path = path
        self.folder_path = os.listdir(path)
        self.file_docs = []
        self.docs_embs = []
        self.retrieve_top_k = 10
        self.rerank_top_k = 3
        self.load()
        self.embed()
        self.index()
    

    def load(self) -> None:
        """
        Loads the documents from the sources and chunks the HTML content.
        """
        print("Loading documents...")

        for folder in self.folder_path:
            small_folder = os.listdir(f"{self.path}/{folder}")
            print(small_folder)
            for file in small_folder:
                elements = partition(filename=f"content/{folder}/{file}")
                chunks = chunk_by_title(elements)
                for chunk in chunks:
                    self.file_docs.append(
                        {
                            "title": f"{file}",
                            "text": str(chunk),
                            "url": f"{self.path}/{file}"
                        }
                    )
    

    def embed(self) -> None:
        """
        Embeds the documents using the Cohere API.
        """
        print("Embedding documents...")

        batch_size = 90
        self.docs_len = len(self.file_docs)

        for i in range(0, self.docs_len, batch_size):
            batch = self.file_docs[i : min(i + batch_size, self.docs_len)]
            texts = [item["text"] for item in batch]
            docs_embs_batch = co.embed(
		              texts=texts,
                      model="embed-english-v3.0",
                      input_type="search_document"
	 		).embeddings
            self.docs_embs.extend(docs_embs_batch)


    def index(self) -> None:
        """
    Indexes the documents for efficient retrieval.
    """
        print("Indexing documents...")

        self.index = hnswlib.Index(space="ip", dim=1024)
        self.index.init_index(max_elements=self.docs_len, ef_construction=512, M=64)
        self.index.add_items(self.docs_embs, list(range(len(self.docs_embs))))

        print(f"Indexing complete with {self.index.get_current_count()} documents.")

    
    def retrieve(self, query: str) -> List[Dict[str, str]]:
        """
        Retrieves documents based on the given query.

        Parameters:
        query (str): The query to retrieve documents for.

        Returns:
        List[Dict[str, str]]: A list of dictionaries representing the retrieved  documents, with 'title', 'snippet', and 'url' keys.
        """
        docs_retrieved = []
        query_emb = co.embed(
                    texts=[query],
                    model="embed-english-v3.0",
                    input_type="search_query"
                    ).embeddings				    

        doc_ids = self.index.knn_query(query_emb, k=self.retrieve_top_k)[0][0]


        docs_to_rerank = []
        for doc_id in doc_ids:
            docs_to_rerank.append(self.file_docs[doc_id]["text"])

        rerank_results = co.rerank(
            query=query,
            documents=docs_to_rerank,
            top_n=self.rerank_top_k,
            model="rerank-english-v2.0",
        )

        doc_ids_reranked = []
        for result in rerank_results:
            doc_ids_reranked.append(doc_ids[result.index])

        for doc_id in doc_ids_reranked:
            docs_retrieved.append(
                {
                    "title": self.file_docs[doc_id]["title"],
                    "text": self.file_docs[doc_id]["text"],
                    "url": self.file_docs[doc_id]["url"],
                }
            )

        return docs_retrieved
