import {
    Button,
    chakra,
    FormControl,
    FormLabel,
    HTMLChakraProps,
    Input,
    Stack,
  } from '@chakra-ui/react'
import * as React from 'react'

export const SignupForm = (props: HTMLChakraProps<'form'>) => (
<chakra.form
    onSubmit={(e) => {
    e.preventDefault()
    // your login logic here
    }}
    {...props}
>
    <Stack spacing="6">
    <FormControl id="email">
        <FormLabel>Email address</FormLabel>
        <Input name="email" type="email" autoComplete="email" required />
    </FormControl>
    <FormControl id="password">
        <FormLabel>Password</FormLabel>
        <Input
            name="password"
            type="password"
            required
        />
    </FormControl>
    <FormControl id="passwordConfirm">
        <FormLabel>Confirm Password</FormLabel>
        <Input
            name="passwordConfirm"
            type="password"
            required
        />
    </FormControl>
    <Button type="submit" colorScheme="blue" size="lg" fontSize="md">
        Sign in
    </Button>
    </Stack>
</chakra.form>
)

