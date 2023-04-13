import { ChatCompletionRequestMessage, Configuration, OpenAIApi } from "openai";
import * as readline from "readline";


let openai: OpenAIApi;
let openAiApiKey: string;
const modelString = "gpt-3.5-turbo";

const maxTokensNumber = 50;
const temperatureNumber = 0.5;

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });
  
function askApiKey(): Promise<string> {
return new Promise((resolve) => {
    rl.question("Please enter your OpenAI API key: ", (apiKey:string) => {
    resolve(apiKey);
    });
});
}

function errorCallback(error: any) {
    console.error("An error occurred:", error);
}


async function fetchWorldSeriesWinner() {
    const messages : ChatCompletionRequestMessage[] = [
        { role: "system", content: "You are a helpful assistant." },
        { role: "user", content: "Who won the world series in 2020?" },
      ];
    try {
        const res = await openai.createChatCompletion({
            model: modelString,
            messages: messages,
            // eslint-disable-next-line @typescript-eslint/naming-convention
            max_tokens: maxTokensNumber,
            temperature: temperatureNumber,
        });

        const answer = res.data.choices[0].message?.content;
        console.log("Answer:", answer);
    } catch (error: any) {
        if (errorCallback) {
            errorCallback(error);
        }
    }
}

async function main() {
    openAiApiKey = await askApiKey();
    rl.close();
  
    const configuration = new Configuration({
      apiKey: openAiApiKey,
    });
  
    openai = new OpenAIApi(configuration);
    await fetchWorldSeriesWinner();
}

main();
