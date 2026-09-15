"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { executeEAAction, getEA } from "@/lib/api";

const EA_ID = "AI_BASKET_EA";

const EA_QUERY_KEY = ["ea", EA_ID] as const;

type EAAction = "start" | "pause" | "resume" | "stop" | "close-basket";

export function useEA() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: EA_QUERY_KEY,

    queryFn: getEA,

    refetchInterval: 2000,

    refetchIntervalInBackground: true,
  });

  const createMutation = (action: EAAction) =>
    useMutation({
      mutationKey: ["ea-action", EA_ID, action],

      mutationFn: () => executeEAAction(action),

      onSuccess: async () => {
        await queryClient.invalidateQueries({
          queryKey: EA_QUERY_KEY,
        });
      },
    });

  const start = createMutation("start");

  const pause = createMutation("pause");

  const resume = createMutation("resume");

  const stop = createMutation("stop");

  const closeBasket = createMutation("close-basket");

  return {
    ...query,

    start,
    pause,
    resume,
    stop,
    closeBasket,

    anyMutationPending:
      start.isPending ||
      pause.isPending ||
      resume.isPending ||
      stop.isPending ||
      closeBasket.isPending,
  };
}
