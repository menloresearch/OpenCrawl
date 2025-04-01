"use server";

import { revalidatePath } from "next/cache";

export type ResearchStatus = {
  task_id: string;
  status: string;
  result: string | null;
  questions: string[] | null;
};

export async function startResearch(query: string): Promise<ResearchStatus> {
  try {
    const response = await fetch("http://localhost:8020/research", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ query }),
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(`Error starting research: ${response.statusText}`);
    }

    const data = await response.json();
    revalidatePath("/");
    return data;
  } catch (error) {
    console.error("Error starting research:", error);
    throw error;
  }
}

export async function getResearchStatus(taskId: string): Promise<ResearchStatus> {
  try {
    const response = await fetch(`http://localhost:8020/research/${taskId}`, {
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(`Error checking status: ${response.statusText}`);
    }

    const data = await response.json();
    revalidatePath("/");
    return data;
  } catch (error) {
    console.error("Error checking research status:", error);
    throw error;
  }
} 