import asyncio
import os
from dotenv import load_dotenv

from collections.abc import Iterator
from goldenverba.components.generation.interface import Generator
from wasabi import msg

load_dotenv()

generate_system_msg = """You are a Retrieval Augmented Generation chatbot. Please answer user queries only their provided context. 
                The context is about the academic programs of the Faculty of Arts and Sciences at Queen's University.
                If the provided documentation does not provide enough information, say so, and explain why. """
            
# rewrite_system_msg = """You are a query augmentation system for the Queen's University Faculty of Arts and Sciences academic program database. 
#                 Your task is to expand the original query question provided to you by the user, providing a better search query 
#                 for database search engine, but no more than two sentences. 
#                   The user will also provide additional document for you to refer to when expanding. 
#                   You can also use your knowledge of Canada higher education system, particularly at Queen's University. 
#                   The new query you generated will be used in a search of Queen's University Faculty of Arts and Sciences Academic Programs database 
#                   (which includes descriptions, requirements, structures, and course offerings for all aspects of academic PROGRAMS, 
#                   as well as related course requirements and descriptions).
                  
#                 Requirements for your response: If you can reason about the answer to the original query directly from the information provided by the user, you can also do so directly.
#                 Otherwise, you can reply with a new augmentation query, 
#                 which should be consistent with the overall form, and semantics of the original query. 
#                 You can also expand the query by expanding the noun element, you can guess, enumerate, explain, 
#                 correct, and expand the keywords of the original query. If there are technical terms or terms related to higher education system, please explain them. 
#                 But you need to focus on what query is asking for. """

# rewrite_examples = """
# The original query:
# What natural language processing related courses are on offer?
# The rewrite query:
# What courses at Queen's University focus on
# natural language processing (NLP), which is a branch of artificial intelligence
# that deals with the interaction between computers and human language?
# Furthermore, include courses that cover topics such as machine learning,
# artificial intelligence, data analytics, and computational linguistics which are
# related fields that contribute to the development and application of NLP
# technologies.
# """


rewrite_system_msg = '''You are a query-answer system for queries about Queen's University Faculty of Arts and Sciences academic program. 
                Your task is to respond to the questions using the documents provided by the user and your knowledge of Queen's University Canada's academic programs.'''
rewrite_examples = '''
                Query: What natural language processing related courses are on offer?
                Passage: Natural language processing (NLP), which is a branch of artificial intelligence
                that deals with the interaction between computers and human language.
                Related courses cover topics such as machine learning, artificial intelligence, data analytics, 
                and computational linguistics which are all relevant to the program. 
                At Queen's University, relevant courses for natural language processing include CISC 352 (Artificial
                Intelligence), CISC 452 (Neural and Genetic Computing), CISC 453 (Topics in
                Artificial Intelligence), CISC 473 (Deep Learning), COGS 201 (Cognition and
                Computation), and LING 415 (Semantics). 

                Query: How to get graduation with First Class Honours? 
                Passage:  The provided context does not include specific information about 
                the criteria for graduating with First Class Honours at Queen's University. 
                Typically, such criteria would involve maintaining a certain grade point average (GPA) 
                or achieving a specific standing in your courses. "How to get graduation with First Class Honours"
                is strongly associated with academic achievements, department specifics, and grading standards.

                Query: List the finance related programs? 
                Passage: Programs related to the field of finance would typically involve the study of 
                economics, accounting, business strategies, and market analysis.
                At Queen's University, the program closest to finance within the 
                Faculty of Arts and Sciences would be Economics, with various levels of study
                such as Economics - Major (Arts) – Bachelor of Arts (Honours), Economics – Joint
                Honours (Arts) – Bachelor of Arts (Honours), and Economics – Minor (Arts).

                Query: How many transfer credits can a student receive at most?
                Passage:
                Questions regarding the maximum number of transfer credits a student can receive are 
                typically found in sections such as "Admission Requirements" or "Transfer Policies," 
                which detail the acceptance criteria and limits for transferring credits into a program.
                Keywords such as “transfer credits,” “credit acceptance,” “maximum transfer credits,” 
                and “transfer policy” can be useful in locating this information. 
                Query: Please compare the main differences between the Art History Joint Honours and Art History General programs
                Passage: The information provided is not sufficient to answer this question fully. 
                However, it can be surmised that The History of Art Joint Honours programme is more 
                specialized, pairing History of Art with another discipline for a Joint Honours degree, 
                whereas the Art History General Programme is less specialized, 
                offering greater flexibility and more electives without leading to an honours degree..
                
                Query: Is the internship available to students from all departments within the Faculty of Arts and Science?
                Passage: The provided documents do not contain specific information regarding the availability of internships to 
                students from all departments within the Faculty of Arts and Science at Queen's
                University. Internship opportunities and their eligibility criteria can vary by
                program and department, and such details are typically outlined in
                program-specific handbooks or on the university's career services website.'''

class Claude3Generator(Generator):
    """
    Generator using Anthropic's Claude-3 model.
    """

    def __init__(self):
        super().__init__()
        self.name = "Claude3Generator"
        self.description = "Generator using Anthropic's Claude-3 model"
        self.requires_library = ["anthropic"]
        self.requires_env = ["ANTHROPIC_API_KEY"]
        self.streamable = True
        self.model_name = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
        self.context_window = 18000

    async def generate(
        self, queries: list[str], context: list[str], conversation: dict = None, generate_rewriting_query: bool = False
    ) -> str:
        if conversation is None:
            conversation = {}

        if generate_rewriting_query:
            messages = self.prepare_rewrite_messages(queries, context, conversation)
            system_msg = rewrite_system_msg
        else:
            messages = self.prepare_messages(queries, context, conversation)
            system_msg = generate_system_msg
        
        #msg.good(f"messages: {messages}")

        total_char_length = sum(len(message["content"]) for message in messages)
        msg.info(f"Total number of characters entered into the {self.name} : {total_char_length}")

        try:
            import anthropic  
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            messages_formatted = messages  # Adjust as needed for Claude

            response = client.messages.create(
                model=self.model_name,
                max_tokens=1024,
                messages=messages_formatted,
                temperature=0.0,
                system = system_msg
            )
            #msg.good(f"Response received: {response}")
            system_msg = str(response.content[0].text)  # Adjust based on Claude's response format
            msg.good(f"Answer generated by {self.name} : {system_msg}")

        except Exception as e:
            print(f"Error during message generation: {e}")
            raise

        return system_msg


    async def generate_stream(self, queries: list[str], context: list[str], conversation: dict = None) -> Iterator[dict]:
        if conversation is None:
            conversation = {}

        messages = self.prepare_messages(queries, context, conversation)
        #msg.good(f"messages: {messages}")

        total_char_length = sum(len(message['content']) for message in messages)
        msg.info(f"Total number of characters entered into the {self.name}: {total_char_length}")

        try:
            import anthropic
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

            with client.messages.stream(
                model=self.model_name,
                max_tokens=1024,
                messages=messages,
                temperature=0.0,
                system=generate_system_msg
            ) as stream:
                for event in stream:
                    # msg.good(f"Event received: {event}")
                    if event.type == 'message_stop':
                        yield {"message": "", "finish_reason": "stop"}  # No more content, stop the stream.
                        break
                    elif event.type == 'content_block_delta':
                        content = event.delta.text  # Extract text content from the event.
                        yield {"message": content, "finish_reason": "continue"}  # Stream continues.
                        # msg.good(f"message content: {content}")
                    elif event.type == 'ping':
                        continue  # Handle ping events, can be used to keep the connection alive.
        except Exception as e:
            print(f"Error during streaming message generation: {e}")
            raise



    def prepare_messages(
        self, queries: list[str], context: list[str], conversation: dict[str, str]
    ) -> list[dict[str, str]]:
        """
        Prepares a list of messages formatted for a Retrieval Augmented Generation chatbot system, including system instructions, previous conversation, and a new user query with context.

        @parameter queries: A list of strings representing the user queries to be answered.
        @parameter context: A list of strings representing the context information provided for the queries.
        @parameter conversation: A list of previous conversation messages that include the role and content.

        @returns A list of message dictionaries formatted for the chatbot. This includes an initial system message, the previous conversation messages, and the new user query encapsulated with the provided context.

        Each message in the list is a dictionary with 'role' and 'content' keys, where 'role' is either 'system' or 'user', and 'content' contains the relevant text. This will depend on the LLM used.
        """
        messages = []



        if conversation and conversation[-1].type == 'user':
            conversation.pop()
            msg.good(f"Successfully popped the last user message from the conversation.")

        #msg.good(f"conversation: {conversation}")

        for message in conversation:
            # 检查message.type的值，如果是"system"则替换为"assistant"
            role = "assistant" if message.type == "system" else message.type
            messages.append({"role": role, "content": message.content})

        query = " ".join(queries)
        user_context = " ".join(context)

        messages.append(
            {
                "role": "user",
                "content": f"""The provided context: {user_context}.               
                These documents are taken from the Queen's University Faculty of Arts and Sciences 
                Academic Programs database, which includes programme descriptions, requirements, 
                structures, and course offerings. The title of the document is between the 
                <document_title></document_title> tags, which represent which programme the document is about.
                 You need to differentiate between program and course, and focus on what the query is asking about.
                 Please answer this query: '{query}' with the provided context.""",
            }
        )


        return messages
    

    def prepare_rewrite_messages(
    self, queries: list[str], context: list[str], conversation: dict[str, str]
        ) -> list[dict[str, str]]:
        """
    Prepares a list of messages formatted for a system focused on enhancing and expanding user queries for more effective database retrieval. It includes system instructions, previous conversation, and a new user query with context aimed at generating a more detailed and comprehensive query.

        @parameter queries: A list of strings representing the user queries to be rewritten for completeness.
        @parameter context: A list of strings representing additional context information provided for the queries.
        @parameter conversation: A list of previous conversation messages that include the role and content.

        @returns A list of message dictionaries formatted to guide the generation of an expanded query. This includes an initial system message, the previous conversation messages, and a prompt for rewriting the user query with the provided additional context.

        Each message in the list is a dictionary with 'role' and 'content' keys, where 'role' is either 'system' or 'user', and 'content' contains the relevant text. This setup is intended to aid large language models in understanding the task of query rewriting.
        """
        messages = []



        #for message in conversation:
        #    messages.append({"role": message.type, "content": message.content})  # Adjusted to use dict access for consistency

        query = " ".join(queries)
        user_context = " ".join(context)

        messages.append(
            {
                "role": "user",
                "content": f"""Additional documents: {user_context}.

                Here are some examples, shown between the <examples></examples> tags.
                <examples>{rewrite_examples}</examples>

                Requirements for your response: Prioritise answering with the information provided by the user.
                and if there is not enough information to answer the question, then use your knowledge about Queen's University 
                Canada's academic programs to answer. 
                When it is not possible to answer a query accurately, the use of synonyms, 
                or the presentation of strongly related concepts, is also encouraged.
                Your answer should be no more than three sentences.
                
                Instructions: Write a passage that answers the given query:

                Query: {query}
                """,

                # "content": f"""Your task is to expand the original query question 
                # provided to you by the user, providing a better search query 
                # for database search engine. Here are some additional documents: {user_context} .
                
                # Here are some examples, shown between the <examples></examples> tags.
                # You can learn the formatting of its answers, and how to rewrite the original query:
                
                # <examples>{rewrite_examples}</examples>

                # Instructions:
                # If you can reason about the answer to the original query directly from the information provided by the user, you can also do so directly. 
                # If the original query is relevant to document information,
                # the use of document information to guess the semantics of the original query, 
                # for element completion and augmentation is encouraged. 
                # if not relevant, use your knowledge about Canada higher education system, especially the education system 
                # of Queen's University, to augment the query. 
                # Using your knowledge, accomplishing the expansion by explaining some of the professional terms or terms 
                # related to higher education system in the original query is encouraged.
                # You can refer to your knowledge about the education system of Queen's University, and the additional document.
                # Based on the original query: '{query}', generate a new rewrite query. """,
            }
        )
        messages.append(
            {
                "role": "assistant",
                "content": "Passage:",
                #"content": "Based on the original query, the rewrite query is",
            }
        )

        return messages
